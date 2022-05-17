import os

from PIL import Image, UnidentifiedImageError
from prompt_toolkit.document import Document
from prompt_toolkit.validation import Validator, ValidationError


class NotEmptyValidator(Validator):
    def __init__(self, label):
        self.label = label

    def validate(self, document: Document):
        if not document.text:
            raise ValidationError(message=f"{self.label} cannot be empty.")


class AdapterKeyValidator(NotEmptyValidator):
    def validate(self, document: Document):
        super().validate(document)
        string = document.text
        if string != self._strip_special_characters(string):
            raise ValidationError(message=f"{self.label} cannot contain special characters.")
        if string[0].isdigit():
            raise ValidationError(message=f"{self.label} cannot begin with a digit.")

    @classmethod
    def _strip_special_characters(cls, string):
        return ''.join(e for e in string if e.isalnum() or e == '_')

    @classmethod
    def default(cls, string):
        default = cls._strip_special_characters(string)
        if default[0].isdigit():
            return "Adapter" + default
        return default


class IntegerValidator(Validator):
    def __init__(self, label):
        self.label = label

    def validate(self, document: Document):
        try:
            if document.text:
                int(document.text)
        except ValueError as e:
            raise ValidationError(message=f"{self.label} must be an integer.")


class NewProjectDirectoryValidator(NotEmptyValidator):
    def validate(self, document: Document):
        super().validate(document)
        dir = document.text
        if os.path.exists(dir) and os.path.isfile(dir):
            raise ValidationError(message=f"{self.label} must be a directory.")
        if os.path.exists(dir) and len(os.listdir(dir)) > 0:
            raise ValidationError(message=f"{self.label} must be empty if it is an existing directory.")


class UniquenessValidator(NotEmptyValidator):
    def __init__(self, label, existing):
        self.existing = existing
        super().__init__(label)

    def validate(self, document: Document):
        super().validate(document)
        string = document.text
        if string in self.existing:
            raise ValidationError(message=f"A {self.label.lower()} with that name already exists.")


class EulaValidator(Validator):
    def validate(self, document: Document):
        file = document.text
        if not (file == "" or os.path.isfile(file)):
            raise ValidationError(message="Path must be a text file.")


class ImageValidator(Validator):
    def validate(self, document: Document):
        img = document.text
        if img == "":
            return
        try:
            if os.path.isdir(img):
                raise ValidationError(message="Path must be an image file.")
            image = Image.open(img, formats=["PNG"])
            if image.size != (256, 256):
                raise ValidationError(
                    message=f"Image must be 256x256 pixels (selected image is {image.size[0]}x{image.size[1]} pixels).")
        except FileNotFoundError:
            raise ValidationError(message="Could not find image file.")
        except TypeError:
            raise ValidationError(message="Image must be in PNG format.")
        except UnidentifiedImageError as e:
            raise ValidationError(message=f"{e}")


class ProjectValidator(Validator):
    def validate(self, document: Document) -> None:
        if not self.is_project_dir(document.text):
            raise ValidationError(message="Path must be a valid Management Pack project directory.")

    @classmethod
    def is_project_dir(cls, path):
        return path is not None and os.path.isdir(path) and os.path.isfile(os.path.join(path, "manifest.txt"))


class ChainValidator(Validator):
    def __init__(self, validators: [Validator]):
        self.validators = validators

    def validate(self, document: Document) -> None:
        for validator in self.validators:
            validator.validate(document)

