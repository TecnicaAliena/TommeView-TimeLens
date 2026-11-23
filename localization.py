import json
import os
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QTranslator
from PySide6.QtWidgets import QApplication, QWidget, QComboBox, QAbstractButton, QLabel

RESOURCES = Path(__file__).parent
CATALOG = json.loads((RESOURCES / 'locales.json').read_text(encoding='utf-8'))


class Translator:
    def __init__(self, preferences):
        self.preferences = Path(preferences)
        self.qt_translator = None
        try:
            data = json.loads(self.preferences.read_text(encoding='utf-8'))
            language = data.get('language', 'it')
        except (OSError, ValueError, AttributeError):
            language = 'it'
        self.language = language if language in ('it', 'en') else 'it'

    def text(self, source, **values):
        text = CATALOG.get(source, {}).get(self.language, source)
        return text.format(**values) if values else text

    def set_language(self, language):
        if language not in ('it', 'en'):
            raise ValueError(language)
        self.preferences.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.preferences.with_suffix('.tmp')
        temporary.write_text(json.dumps({'language': language}), encoding='utf-8')
        os.replace(temporary, self.preferences)
        self.language = language

    def widgets(self, root):
        # Only catalogued UI literals are translated; media filenames are excluded.
        reverse = {value: key for key, entry in CATALOG.items() for value in entry.values()}
        def localized(value):
            return self.text(reverse.get(value, value))
        for widget in [root, *root.findChildren(QWidget)]:
            if widget.property('i18n_skip'):
                continue
            if isinstance(widget, (QAbstractButton, QLabel)):
                widget.setText(localized(widget.text()))
            if widget.toolTip():
                widget.setToolTip(localized(widget.toolTip()))
            if widget.windowTitle():
                widget.setWindowTitle(localized(widget.windowTitle()))
            if isinstance(widget, QComboBox):
                for index in range(widget.count()):
                    widget.setItemText(index, localized(widget.itemText(index)))

    def activate_qt(self):
        app = QApplication.instance()
        if self.qt_translator is not None:
            app.removeTranslator(self.qt_translator)
        self.qt_translator = QTranslator(app)
        if self.language == 'it':
            for folder in (RESOURCES / 'translations', Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))):
                if self.qt_translator.load(str(folder / 'qtbase_it.qm')):
                    app.installTranslator(self.qt_translator)
                    break
