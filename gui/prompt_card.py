import logging
import time
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMenu,
    QApplication,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QMouseEvent, QContextMenuEvent

logger = logging.getLogger(__name__)


class PromptCard(QWidget):
    clicktime = 100  # (milliseconds)

    def __init__(self, parent, prompt, on_click, on_edit, on_delete):
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
        self.original_position = None
        self.drag_start_position = None
        self.drag_start_time = None

        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
        """)

        self.setup_ui()

        # Bind events to the main widget
        self.mousePressEvent = self.on_card_click
        self.mouseDoubleClickEvent = self.on_card_click
        self.contextMenuEvent = self.on_right_click
        self.mouseMoveEvent = self.on_mouse_move
        self.mouseReleaseEvent = self.on_mouse_up

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(5)

        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(5)

        # Header with bold font
        header = QLabel(self.prompt["name"])
        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(11)
        header.setFont(header_font)
        header.setStyleSheet("color: #4682B4;")  # Steel blue
        header.setWordWrap(True)

        prompt_layout.addWidget(header)

        # Content - first few lines
        content_lines = self.prompt["content"].split("\n")
        content_preview = "\n".join(content_lines[:1])  # First line
        if len(content_lines) > 3:
            content_preview += "\n..."

        content = QLabel(content_preview)
        content.setWordWrap(True)
        content.setMinimumWidth(300)
        prompt_layout.addWidget(content)

        main_layout.addLayout(prompt_layout)

        # Tags as blobs
        if self.prompt.get("tags"):
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(4)
            for tag in self.prompt["tags"]:
                tag_blob = QPushButton(f"#{tag}")
                tag_blob.setStyleSheet("""
                    QPushButton {
                        background-color: #f0f0f0;
                        color: black;
                        border: none;
                        border-radius: 11px;
                        padding: 2px 8px;
                        font-size: 12px;
                        min-height: 22px;
                    }
                    QPushButton:hover {
                        background-color: #e0e0e0;
                    }
                """)
                # Bind click to copy tag to search
                tag_blob.clicked.connect(
                    lambda checked, t=tag: self.copy_tag_to_search(t)
                )
                tags_layout.addWidget(tag_blob)
            tags_layout.addStretch()
            main_layout.addLayout(tags_layout)

        self.setLayout(main_layout)
        self.setFixedHeight(120)

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

    def on_card_click(self, event):
        """Handle card click event - start drag operation"""
        logger.debug("Mouse down event detected")
        try:
            if event.button() == Qt.MouseButton.LeftButton and not self.dragging:
                self.dragging = True
                self.original_position = self.pos()
                if isinstance(event, QMouseEvent):
                    self.drag_start_position = event.pos()
                else:
                    self.drag_start_position = QPoint(0, 0)
                self.drag_start_time = (
                    time.time_ns() // 1000000
                )  # Convert to milliseconds
                self.raise_()  # Bring the widget to the front
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error handling card click: {e}")
        # Don't call super() for custom event handling

    def on_right_click(self, event):
        """Show context menu"""
        if self.dragging:
            # If dragging, ignore right click to avoid context menu during drag
            return
        try:
            from PyQt6.QtWidgets import QMenu

            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                }
                QMenu::item {
                    padding: 4px 20px;
                }
                QMenu::item:selected {
                    background-color: #4a90e2;
                    color: white;
                }
            """)

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
                        from PyQt6.QtWidgets import QMessageBox

                        QMessageBox.warning(self, "Error", "Edit callback not set")
                except Exception as e:
                    from PyQt6.QtWidgets import QMessageBox

                    QMessageBox.critical(self, "Error", f"Error editing prompt: {e}")

            def on_delete():
                try:
                    from PyQt6.QtWidgets import QMessageBox

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
                    from PyQt6.QtWidgets import QMessageBox

                    QMessageBox.critical(
                        self, "Error", f"Error in delete confirmation: {e}"
                    )
                    logger.error(f"Detailed confirmation error: {e}")

            def on_copy_content():
                try:
                    if self.on_click:  # Check if callback exists
                        self.on_click(self.prompt)  # This copies to clipboard
                    else:
                        from PyQt6.QtWidgets import QMessageBox

                        QMessageBox.warning(self, "Error", "Copy callback not set")
                except Exception as e:
                    from PyQt6.QtWidgets import QMessageBox

                    QMessageBox.critical(self, "Error", f"Error copying content: {e}")

            # Connect menu actions
            edit_item.triggered.connect(on_edit)
            delete_item.triggered.connect(on_delete)
            copy_content_item.triggered.connect(on_copy_content)

            # Show the popup menu
            if isinstance(event, QContextMenuEvent):
                menu.exec(event.globalPos())
            else:
                from PyQt6.QtGui import QCursor

                menu.exec(QCursor.pos())

        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(self, "Error", f"Error showing context menu: {e}")
            logger.error(f"Detailed menu error: {e}")

    def on_mouse_move(self, event):
        """Handle mouse move events for dragging"""
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            try:
                # Calculate new position based on the initial offset
                parent = self.parent()
                if parent:
                    # Convert global position to parent coordinates
                    global_pos = event.globalPosition().toPoint()
                    parent_pos = parent.mapFromGlobal(global_pos)
                    new_pos = parent_pos - self.drag_start_position

                    # Move the widget
                    self.move(new_pos)
                    self.raise_()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
            except Exception as e:
                logger.error(f"Error during drag move: {e}")

        super().mouseMoveEvent(event)

    def on_mouse_up(self, event):
        """Stop dragging the prompt card or finalize click"""
        logger.debug("Mouse up event detected")
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.dragging:
                    self.dragging = False
                    # Return to the original position after dragging
                    self.move(self.original_position)
                    self.setCursor(Qt.CursorShape.ArrowCursor)

                # Check if it was a quick click (not a drag)
                if (
                    hasattr(self, "drag_start_time")
                    and (time.time_ns() // 1000000 - self.drag_start_time)
                    < self.clicktime
                ):
                    # Call the click callback only if it wasn't a significant drag
                    try:
                        if self.on_click:  # Check if callback exists
                            self.on_click(self.prompt)  # This copies to clipboard
                        else:
                            logger.warning("Click callback not set")
                    except Exception as e:
                        from PyQt6.QtWidgets import QMessageBox

                        QMessageBox.critical(
                            self, "Error", f"Error handling card click: {e}"
                        )
        except Exception as e:
            logger.error(f"Error in mouse up handler: {e}")

        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter event - visual feedback"""
        try:
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border: 1px solid #a0a0a0;
                    border-radius: 4px;
                }
            """)
        except Exception as e:
            logger.error(f"Error in enter event: {e}")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave event - restore normal appearance"""
        try:
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                }
            """)
        except Exception as e:
            logger.error(f"Error in leave event: {e}")
        super().leaveEvent(event)
