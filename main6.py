import os
from main import BlockSpace

BLOCK_SIZES = [2 ** i for i in range(10, 17)]

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

        num_blocks = int(input("Введите количество блоков для файла: "))
        block_size = int(input("Введите размер блока (в байтах): "))

        # Убедимся, что размер блока соответствует допустимым значениям
        if block_size not in BLOCK_SIZES:
            raise Exception("Недопустимый размер блока. Выберите размер из допустимых значений.")

        blocks = self.block_space.allocate_blocks(num_blocks)
        if not blocks:
            raise Exception("Недостаточно свободных блоков.")

        self.files[full_path] = {"size": 0, "blocks": blocks, "position": 0, "block_size": block_size}
        self.directories[self.current_dir].append(name)
        print(f"Файл {name} создан с {num_blocks} блоками по {block_size} байт.")

    def open_file(self, name):
        full_path = self.get_full_path(name)
        if full_path not in self.files:
            raise Exception("Файл не найден.")
        return self.files[full_path]

    def write_file(self, name, data):
        file = self.open_file(name)
        blocks_needed = (len(data) + file["block_size"] - 1) // file["block_size"]

        while len(file["blocks"]) < blocks_needed:
            new_blocks = self.block_space.allocate_blocks(1)
            if not new_blocks:
                raise Exception("Недостаточно свободных блоков для записи.")
            file["blocks"].extend(new_blocks)

        # Запрашиваем номер блока для записи
        block_index = int(input(f"Введите номер блока (0 до {len(file['blocks']) - 1}) для записи данных: "))
        if block_index < 0 or block_index >= len(file["blocks"]):
            raise Exception("Недопустимый номер блока.")

        self.block_space.write_data(data, [file["blocks"][block_index]])
        file["size"] = len(data)
        file["position"] = len(data)
        print(f"Данные записаны в блок {block_index} файла {name}.")

    def read_file(self, name):
        file = self.open_file(name)

        # Запрашиваем номер блока для чтения
        block_index = int(input(f"Введите номер блока (0 до {len(file['blocks']) - 1}) для чтения данных: "))
        if block_index < 0 or block_index >= len(file["blocks"]):
            raise Exception("Недопустимый номер блока.")

        # Читаем данные из выбранного блока
        buffer = bytearray(file["block_size"])
        self.block_space.read_data([file["blocks"][block_index]], buffer)
        print(f"Данные из блока {block_index} файла {name}: {buffer.decode('utf-8', errors='ignore')}")

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
        items = []
        for name in self.directories[self.current_dir]:
            full_path = self.get_full_path(name)
            if full_path in self.files:
                items.append(f"{name} (файл)")
            else:
                items.append(f"{name} (каталог)")
        return items

    def import_file(self, src_path, dest_name):
        if not os.path.exists(src_path):
            raise Exception("Исходный файл не найден.")
        with open(src_path, 'rb') as f:
            data = f.read()
        self.create_file(dest_name)
        self.write_file(dest_name, data)
        print(f"Файл {src_path} импортирован как {dest_name}.")

def main():
    with open("block_space.bin", 'wb') as f:
        f.write(b'')

    block_space = BlockSpace("block_space.bin", 1024, 100)
    fs = FileSystem(block_space)

    while True:
        print(f"\nТекущий каталог: {fs.current_dir}")
        print("Выберите действие:")
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
                fs.read_file(name)

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

