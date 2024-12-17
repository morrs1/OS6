import os
from main import BlockSpace

class FileSystem:
    def __init__(self, block_space):
        self.block_space = block_space
        self.files = {}
        self.directories = {"/": []}
        self.current_dir = "/"

    def get_full_path(self, name):
        return os.path.join(self.current_dir, name)

    def create_file(self, name):
        full_path = self.get_full_path(name)
        if full_path in self.files or name in self.directories[self.current_dir]:
            raise Exception("Файл с таким именем уже существует или имя занято каталогом.")

        blocks = self.block_space.allocate_blocks(1)  # Зарезервируем 1 блок под метаданные
        if not blocks:
            raise Exception("Недостаточно свободных блоков.")

        self.files[full_path] = {"size": 0, "blocks": blocks, "position": 0}
        self.directories[self.current_dir].append(name)
        print(f"Файл {name} создан.")

    def open_file(self, name):
        full_path = self.get_full_path(name)
        if full_path not in self.files:
            raise Exception("Файл не найден.")
        return self.files[full_path]

    def write_file(self, name, data):
        file = self.open_file(name)
        blocks_needed = (len(data) + self.block_space.block_size - 1) // self.block_space.block_size

        while len(file["blocks"]) < blocks_needed:
            new_blocks = self.block_space.allocate_blocks(1)
            if not new_blocks:
                raise Exception("Недостаточно свободных блоков для записи.")
            file["blocks"].extend(new_blocks)

        self.block_space.write_data(data, file["blocks"][:blocks_needed])
        file["size"] = len(data)
        file["position"] = len(data)
        print(f"Данные записаны в файл {name}.")

    def read_file(self, name, length):
        file = self.open_file(name)
        buffer = bytearray(length)
        self.block_space.read_data(file["blocks"], buffer)
        return buffer[:file["size"]]

    def delete_file(self, name):
        full_path = self.get_full_path(name)
        if full_path not in self.files:
            raise Exception("Файл не найден.")

        file = self.files.pop(full_path)
        self.block_space.release_blocks(file["blocks"])
        self.directories[self.current_dir].remove(name)
        print(f"Файл {name} удалён.")

    def create_directory(self, name):
        path = self.get_full_path(name)
        if path in self.directories:
            raise Exception("Каталог уже существует.")
        self.directories[path] = []
        self.directories[self.current_dir].append(name)
        print(f"Каталог {name} создан.")

    def delete_directory(self, name):
        path = self.get_full_path(name)
        if path not in self.directories:
            raise Exception("Каталог не найден.")
        if self.directories[path]:
            raise Exception("Каталог не пуст.")
        del self.directories[path]
        self.directories[self.current_dir].remove(name)
        print(f"Каталог {name} удалён.")

    def change_directory(self, name):
        if name == "..":
            if self.current_dir == "/":
                raise Exception("Невозможно выйти из корневого каталога.")
            self.current_dir = os.path.dirname(self.current_dir)
        else:
            path = self.get_full_path(name)
            if path not in self.directories:
                raise Exception("Каталог не найден.")
            self.current_dir = path
        print(f"Текущий каталог изменён на {self.current_dir}.")

    def list_directory(self):
        return self.directories[self.current_dir]

    def import_file(self, src_path, dest_name):
        if not os.path.exists(src_path):
            raise Exception("Исходный файл не найден.")
        with open(src_path, 'rb') as f:
            data = f.read()
        self.create_file(dest_name)
        self.write_file(dest_name, data)
        print(f"Файл {src_path} импортирован как {dest_name}.")

def main():
    block_space = BlockSpace("block_space.bin", 1024, 100)  # Создаём блочное пространство
    fs = FileSystem(block_space)

    while True:
        print("\nВыберите действие:")
        print("1 - Создать файл")
        print("2 - Записать данные в файл")
        print("3 - Считать данные из файла")
        print("4 - Удалить файл")
        print("5 - Создать каталог")
        print("6 - Удалить каталог")
        print("7 - Сменить каталог")
        print("8 - Список содержимого каталога")
        print("9 - Импортировать файл")
        print("10 - Выход")

        choice = input("Введите номер действия: ")

        try:
            if choice == '1':
                name = input("Введите имя файла: ")
                fs.create_file(name)

            elif choice == '2':
                name = input("Введите имя файла: ")
                data = input("Введите данные: ").encode('utf-8')
                fs.write_file(name, data)

            elif choice == '3':
                name = input("Введите имя файла: ")
                length = int(input("Введите количество байт для чтения: "))
                data = fs.read_file(name, length)
                print("Считанные данные:", data.decode('utf-8', errors='ignore'))

            elif choice == '4':
                name = input("Введите имя файла: ")
                fs.delete_file(name)

            elif choice == '5':
                name = input("Введите имя каталога: ")
                fs.create_directory(name)

            elif choice == '6':
                name = input("Введите имя каталога: ")
                fs.delete_directory(name)

            elif choice == '7':
                name = input("Введите имя каталога или '..' для возврата: ")
                fs.change_directory(name)

            elif choice == '8':
                print("Содержимое каталога:", fs.list_directory())

            elif choice == '9':
                src_path = input("Введите путь к исходному файлу: ")
                dest_name = input("Введите имя для сохранения: ")
                fs.import_file(src_path, dest_name)

            elif choice == '10':
                print("Выход из программы.")
                break

            else:
                print("Неверный выбор. Пожалуйста, попробуйте снова.")

        except Exception as e:
            print("Ошибка:", str(e))

if __name__ == "__main__":
    main()
