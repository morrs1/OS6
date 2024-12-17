class VirtualFile:
    def __init__(self, name):
        if len(name) > 256:
            raise ValueError("File name exceeds the limit of 256 characters.")
        self.name = name
        self.content = bytearray()
        self.position = 0

class VirtualFileSystem:
    def __init__(self):
        self.files = {}
        self.directories = {"/": []}
        self.current_directory = "/"

    def create_file(self, file_path):
        path, name = self._split_path(file_path)
        if name in self.directories.get(path, []):
            raise FileExistsError("File already exists.")
        self.files[file_path] = VirtualFile(name)
        self.directories[path].append(name)

    def open_file(self, file_path):
        if file_path not in self.files:
            raise FileNotFoundError("File not found.")
        return self.files[file_path]

    def move_file_position(self, file_obj, position):
        if position < 0 or position > len(file_obj.content):
            raise ValueError("Position out of bounds.")
        file_obj.position = position

    def read_file(self, file_obj, length):
        start = file_obj.position
        end = min(file_obj.position + length, len(file_obj.content))
        file_obj.position = end
        return file_obj.content[start:end]

    def write_file(self, file_obj, data):
        start = file_obj.position
        end = start + len(data)
        if end > len(file_obj.content):
            file_obj.content.extend(b"\x00" * (end - len(file_obj.content)))
        file_obj.content[start:end] = data
        file_obj.position = end

    def delete_file(self, file_path):
        path, name = self._split_path(file_path)
        if file_path in self.files:
            del self.files[file_path]
            self.directories[path].remove(name)
        else:
            raise FileNotFoundError("File not found.")

    def find_files(self, directory, mask="*.*"):
        import fnmatch
        if directory not in self.directories:
            raise FileNotFoundError("Directory not found.")
        return [f for f in self.directories[directory] if fnmatch.fnmatch(f, mask)]

    def create_directory(self, directory):
        path, name = self._split_path(directory)
        if directory in self.directories:
            raise FileExistsError("Directory already exists.")
        if path not in self.directories:
            raise FileNotFoundError("Parent directory not found.")
        self.directories[directory] = []
        self.directories[path].append(name)

    def delete_directory(self, directory):
        if directory not in self.directories:
            raise FileNotFoundError("Directory not found.")
        if self.directories[directory]:
            raise OSError("Directory is not empty.")
        del self.directories[directory]
        path, name = self._split_path(directory)
        self.directories[path].remove(name)

    def change_directory(self, directory):
        if directory not in self.directories:
            raise FileNotFoundError("Directory not found.")
        self.current_directory = directory

    def get_current_directory(self):
        return self.current_directory

    def import_data(self, data, target_path):
        path, name = self._split_path(target_path)
        if path not in self.directories:
            raise FileNotFoundError("Target directory not found.")
        if target_path not in self.files:
            self.create_file(target_path)
        file_obj = self.files[target_path]
        file_obj.content = bytearray(data)

    def _split_path(self, path):
        if "/" not in path:
            return "/", path
        parts = path.rsplit("/", 1)
        return parts[0] if parts[0] else "/", parts[1]

# Example usage:
vfs = VirtualFileSystem()
vfs.create_directory("/documents")
vfs.create_file("/documents/file1.txt")
file = vfs.open_file("/documents/file1.txt")
vfs.write_file(file, b"Hello, World!")
print(vfs.read_file(file, 100))
