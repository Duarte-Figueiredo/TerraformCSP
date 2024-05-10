import os
from typing import Union, Any


def flat_list_dicts_to_dict(l: list[dict[str, any]]) -> dict[str, any]:
    result: dict[str, any] = {}

    item: Union[list, dict[str, Any]]
    for item in l:
        next_dict: dict[str, Any]
        if type(item) is list:
            next_dict = flat_list_dicts_to_dict(item)
        elif type(item) is dict:
            next_dict = item
        else:
            raise RuntimeError(f"Unexpected type '{type(item)}")

        result.update(next_dict)

    return result


def resolve_path_local_reference(path: str, local_reference: str) -> str:
    abs_path = os.path.abspath(f"{path}/{local_reference}")

    return abs_path


def extract_key_values_from_any(requested_key: str, obj: Union[list, dict]) -> [str]:
    result: [str] = []
    if type(obj) is list:
        for val in obj:
            result.extend(extract_key_values_from_any(requested_key, val))
    elif type(obj) is dict:
        if requested_key in obj:
            result.append(obj[requested_key])
        else:
            for key, val in obj.items():
                if requested_key == key:
                    if type(val) is str:
                        result.append(val)
                    else:
                        raise RuntimeError(f"Unexpected type {type(val)}")
                else:
                    result.extend(extract_key_values_from_any(requested_key, val))
    elif type(obj) in [int, bool, str]:
        return []
    else:
        raise RuntimeError(f"Unexpected type {type(obj)}")

    return result
