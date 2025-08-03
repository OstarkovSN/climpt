import logging
import time
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMenu,
    QApplication,
    QFrame,
)
from PySide6.QtCore import Qt, QPoint, Signal, QMimeData
from PySide6.QtGui import QFont, QCursor, QMouseEvent, QContextMenuEvent
from PySide6.QtGui import QDrag, QPixmap
from gui.styles import style_manager

logger = logging.getLogger(__name__)


class PromptCard(QFrame):
    clicktime = 100  # (milliseconds)
    card_moved = Signal(int, int)

    def __init__(
        self,
        parent,
        prompt,
        on_click,
        on_edit,
        on_delete,
        original_index,
        current_index,
    ):
        """
        Constructor for PromptCard.

        Args:
            parent: The parent widget for this PromptCard.
            prompt: The prompt data to display in this card.
            on_click: Callable to run when this card is clicked.
            on_edit: Callable to run when the edit button is clicked.
            on_delete: Callable to run when the delete button is clicked.
        """
        super().__init__(parent)
        self.prompt = prompt
        self.on_click = on_click
        self.on_edit = on_edit
        self.on_delete = on_delete  # This is MainFrame.delete_prompt
        self.dragging = False
        self.drag_start_position = None
        self.original_index = original_index
        self.current_index = current_index
        self.setAcceptDrops(True)
        self.setup_ui()

    def cleanup(self):
        logger.debug("triggering cleanup for PromptCard")
        self.card_moved.disconnect()
        self.deleteLater()

    def setup_ui(self):
        wrapper = QWidget()
        wrapper.setObjectName("PromptCard")
        style_manager.attach(wrapper, "prompt_card")

        main_layout = QVBoxLayout()
        main_layout.addStretch()

        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(5)

        # Header with bold font
        header = QLabel(self.prompt["name"])
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(11)
        header.setFont(header_font)
        style_manager.attach(header, "prompt_header")
        header.setWordWrap(True)

        prompt_layout.addWidget(header)

        # Content - first few lines
        content_lines = self.prompt["content"].split("\n")
        content_preview = "\n".join(content_lines[:3])  # First three lines
        if len(content_lines) > 3:
            content_preview += "..."

        content = QLabel(content_preview)
        content.setWordWrap(True)
        content.setMinimumWidth(300)
        content.setMinimumHeight(80)
        prompt_layout.addWidget(content)
        style_manager.attach(content, "prompt_card_content")

        main_layout.addLayout(prompt_layout)

        # Tags as blobs
        if self.prompt.get("tags"):
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            for tag in self.prompt["tags"]:
                tag_blob = QPushButton(f"#{tag}")
                style_manager.attach(tag_blob, "tag_blob")
                # Bind click to copy tag to search
                tag_blob.clicked.connect(
                    lambda checked, t=tag: self.copy_tag_to_search(t)
                )
                tags_layout.addWidget(tag_blob)
            tags_layout.addStretch()
            main_layout.addLayout(tags_layout)

        wrapper.setLayout(main_layout)
        wrapper.setFixedHeight(150)
        layout = QVBoxLayout()
        layout.addWidget(wrapper)
        self.setLayout(layout)
        self.raise_()

    def copy_tag_to_search(self, tag):
        """Copy tag to search box"""
        try:
            # Find the main window to access search control
            parent = self.parent()
            while parent and not hasattr(parent, "search_ctrl"):
                parent = parent.parent()

            if parent and hasattr(parent, "search_ctrl"):
                search_ctrl = parent.search_ctrl
                search_ctrl.setText(f"#{tag}")

                # Trigger search
                if hasattr(parent, "on_search"):
                    parent.on_search()
            else:
                logger.error("Could not find search control in parent hierarchy")
        except Exception as e:
            logger.error(f"Error copying tag to search: {e}")

    def contextMenuEvent(self, event):
        """Show context menu"""
        if self.dragging:
            # If dragging, ignore right click to avoid context menu during drag
            return
        try:
            from PySide6.QtWidgets import QMenu

            menu = QMenu(self)
            style_manager.attach(menu, "context_menu")

            edit_item = menu.addAction("Edit Prompt")
            delete_item = menu.addAction("Delete Prompt")

            # Add separator and copy content option
            menu.addSeparator()
            copy_content_item = menu.addAction("Copy Content")

            def on_edit():
                try:
                    if self.on_edit:  # Check if callback exists
                        self.on_edit(self.prompt)
                    else:
                        from PySide6.QtWidgets import QMessageBox

                        QMessageBox.warning(self, "Error", "Edit callback not set")
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.critical(self, "Error", f"Error editing prompt: {e}")

            def on_delete():
                try:
                    from PySide6.QtWidgets import QMessageBox

                    # Show confirmation dialog
                    reply = QMessageBox.question(
                        self,
                        "Confirm Delete",
                        f"Are you sure you want to delete '{self.prompt['name']}'?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        # Ensure the callback exists before calling
                        if self.on_delete:
                            # Call the delete callback passed from MainFrame
                            try:
                                self.on_delete(self.prompt["id"])
                            except Exception as delete_error:
                                QMessageBox.critical(
                                    self,
                                    "Error",
                                    f"Error deleting prompt in callback: {delete_error}",
                                )
                                logger.error(f"Detailed delete error: {delete_error}")
                        else:
                            QMessageBox.warning(
                                self, "Error", "Delete callback not set"
                            )

                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.critical(
                        self, "Error", f"Error in delete confirmation: {e}"
                    )
                    logger.error(f"Detailed confirmation error: {e}")

            def on_copy_content():
                try:
                    if self.on_click:  # Check if callback exists
                        self.on_click(self.prompt)  # This copies to clipboard
                    else:
                        from PySide6.QtWidgets import QMessageBox

                        QMessageBox.warning(self, "Error", "Copy callback not set")
                except Exception as e:
                    from PySide6.QtWidgets import QMessageBox

                    QMessageBox.critical(self, "Error", f"Error copying content: {e}")

            # Connect menu actions
            edit_item.triggered.connect(on_edit)
            delete_item.triggered.connect(on_delete)
            copy_content_item.triggered.connect(on_copy_content)

            # Show the popup menu
            if isinstance(event, QContextMenuEvent):
                menu.exec(event.globalPos())
            else:
                from PySide6.QtGui import QCursor

                menu.exec(QCursor.pos())

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error showing context menu: {e}")
            logger.error(f"Detailed menu error: {e}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.position().toPoint()
            self.dragging = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (
            event.position().toPoint() - self.drag_start_position
        ).manhattanLength() < 10:
            return
        self.dragging = True
        # Create drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.current_index))
        drag.setMimeData(mime_data)

        # Create pixmap for visual feedback
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.position().toPoint())

        # Execute drag operation
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            from_index = int(event.mimeData().text())
            logger.debug(
                f"Emitting card moved signal from {from_index} to {self.current_index}"
            )
            self.card_moved.emit(from_index, self.current_index)
            event.acceptProposedAction()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.dragging:
            # Handle click event
            if hasattr(self, "on_click") and callable(self.on_click):
                self.on_click(self.prompt)
