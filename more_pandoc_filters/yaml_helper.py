from typing import Any

import yaml


class YamlHelper:

    @classmethod
    def read_yaml(cls, file_path: str) -> Any:
        with open(file_path, 'r') as f:
            yaml_properties: Any = yaml.safe_load(f)
            return yaml_properties

    @classmethod
    def read_yaml_properties_by_key(cls, file_path: str, custom_property_key: str) -> Any:
        """Mapper for reading a specific property from a YAML file.
        :param file_path: The path to the YAML file.
        :param custom_property_key: The key of the property to read.
        :returns The value of the specified property.
        """
        return cls.read_yaml(file_path)[custom_property_key]