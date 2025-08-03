from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QWidget
)
import logging

logger = logging.getLogger(__name__)


class EditPromptDialog(QDialog):
    def __init__(self, parent, prompt=None):
        title = "Edit Prompt" if prompt else "Add New Prompt"
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 400)

        self.prompt = prompt or {"id": None, "name": "", "content": "", "tags": []}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Name
        name_label = QLabel("Name:")
        self.name_ctrl = QLineEdit(self.prompt["name"])
        layout.addWidget(name_label)
        layout.addWidget(self.name_ctrl)

        # Content
        content_label = QLabel("Content:")
        self.content_ctrl = QTextEdit()
        self.content_ctrl.setPlainText(self.prompt["content"])
        self.content_ctrl.setMinimumHeight(150)
        layout.addWidget(content_label)
        layout.addWidget(self.content_ctrl)

        # Tags
        tags_label = QLabel("Tags (comma separated):")
        tags_str = ", ".join(self.prompt["tags"])
        self.tags_ctrl = QLineEdit(tags_str)
        layout.addWidget(tags_label)
        layout.addWidget(self.tags_ctrl)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn.clicked.connect(self.on_cancel)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def on_ok(self):
        self.accept()

    def on_cancel(self):
        self.reject()

    def get_data(self):
        tags_str = self.tags_ctrl.text()
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

        return {
            "id": self.prompt["id"],
            "name": self.name_ctrl.text(),
            "content": self.content_ctrl.toPlainText(),
            "tags": tags,
        }