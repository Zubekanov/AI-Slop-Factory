import os

class PathVerifier:
    base_dir    = None

    def __init__(self):
        # Base directory is two directories above the current file.
        self.base_dir = self.get_base_dir()

    @staticmethod
    def get_base_dir():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def path_to_dict_abs(path: str):
        result = {}
        result['name'] = os.path.basename(path)
        if os.path.isdir(path):
            result['type'] = "dir"
            result['contents'] = [PathVerifier.path_to_dict_abs(contents) for contents in os.listdir(path)]
        else:
            result['type'] = "file"
        
        return result

    def path_to_dict_rel(self, path: str = None):
        abs_path = self.base_dir if (path == None) else os.path.join(self.base_dir, path)
        return self.path_to_dict_abs(abs_path)

    @staticmethod
    def construct_from_json():
        pass

if __name__ == "__main__":
    test = PathVerifier()
    print(test.path_to_dict_rel())