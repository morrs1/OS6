import os
import struct

MIN_BLOCK_SIZE = 2 ** 10
MAX_BLOCK_SIZE = 2 ** 16
BLOCK_SIZES = [2 ** i for i in range(10, 17)]

class FreeBlockChain:
    def __init__(self, start_block, block_count):
        self.start_block = start_block
        self.block_count = block_count
        self.next = None

    def __str__(self):
        return f"({self.start_block}, {self.block_count})"

class BlockSpace:
    def __init__(self, filename, block_size, total_blocks):
        self.filename = filename
        self.block_size = block_size
        self.total_blocks = total_blocks
        self.allocated_blocks = {}
        self.free_blocks_head = None
        self.transaction_cache = {}
        self.transaction_active = False

        self.initialize_free_blocks()

    def block_space_info(self):
        free_chains = []
        free_count = 0
        current = self.free_blocks_head
        while current:
            free_count += current.block_count
            free_chains.append(str(current))
            current = current.next

        return {
            'block_size': self.block_size,
            'total_blocks': self.total_blocks,
            'free_blocks': free_count,
            'free_block_chains': free_chains,
            'allocated_blocks': self.total_blocks - free_count,
            'service_memory_size': len(self.allocated_blocks) * self.block_size,
            'transaction_cache_size': sum(len(data) for data in self.transaction_cache.values())
        }

    def initialize_free_blocks(self):
        self.free_blocks_head = FreeBlockChain(0, self.total_blocks)

    def start_transaction(self):
        if self.transaction_active:
            print("Транзакция уже активна.")
            return
        self.transaction_cache.clear()
        self.transaction_active = True
        print("Транзакция начата.")

    def commit_transaction(self):
        if not self.transaction_active:
            print("Нет активной транзакции для фиксации.")
            return

        with open(self.filename, 'r+b') as f:
            for index, data in self.transaction_cache.items():
                f.seek(index * self.block_size)
                f.write(data)

        self.transaction_cache.clear()
        self.transaction_active = False
        print("Транзакция зафиксирована.")

    def rollback_transaction(self):
        if not self.transaction_active:
            print("Нет активной транзакции для отката.")
            return

        self.transaction_cache.clear()
        self.transaction_active = False
        print("Транзакция отменена.")

    def write_data(self, data, block_indices):
        data_length = len(data)
        if self.transaction_active:
            for block_index in block_indices:
                if block_index in self.allocated_blocks:
                    start = (block_index - block_indices[0]) * self.block_size
                    end = start + self.block_size
                    block_data = data[start:end] if start < data_length else b'\x00' * self.block_size
                    self.transaction_cache[block_index] = block_data
            print(f"Данные записаны в кеш для блоков: {block_indices}")
        else:
            with open(self.filename, 'r+b') as f:
                for block_index in block_indices:
                    if block_index in self.allocated_blocks:
                        start = (block_index - block_indices[0]) * self.block_size
                        end = start + self.block_size
                        block_data = data[start:end] if start < data_length else b'\x00' * self.block_size
                        f.seek(block_index * self.block_size)
                        f.write(block_data)
            print(f"Данные записаны в файл для блоков: {block_indices}")

    def read_data(self, block_indices, buffer):
        with open(self.filename, 'rb') as f:
            for i, block_index in enumerate(block_indices):
                if block_index in self.transaction_cache:
                    buffer[i * self.block_size:(i + 1) * self.block_size] = self.transaction_cache[block_index]
                else:
                    f.seek(block_index * self.block_size)
                    buffer[i * self.block_size:(i + 1) * self.block_size] = f.read(self.block_size)

    def allocate_blocks(self, num_blocks):
        if num_blocks <= 0:
            return []

        allocated = []

        current_chain = self.free_blocks_head
        while current_chain and num_blocks > 0:
            if current_chain.block_count >= num_blocks:
                allocated.extend(range(current_chain.start_block, current_chain.start_block + num_blocks))
                if current_chain.block_count > num_blocks:

                    current_chain.start_block += num_blocks
                    current_chain.block_count -= num_blocks
                else:

                    if current_chain == self.free_blocks_head:
                        self.free_blocks_head = current_chain.next
                    else:
                        prev_chain.next = current_chain.next

                break

            prev_chain = current_chain
            current_chain = current_chain.next

        for block in allocated:
            self.allocated_blocks[block] = bytearray(self.block_size)

        return allocated

    def release_blocks(self, block_indices):
        for block_index in block_indices:
            if block_index in self.allocated_blocks:
                del self.allocated_blocks[block_index]

                current_chain = self.free_blocks_head
                while current_chain:
                    if current_chain.start_block == block_index + 1:  # Проверяем, можно ли объединить с предыдущей цепочкой
                        current_chain.start_block -= 1
                        current_chain.block_count += 1
                        break
                    elif current_chain.start_block + current_chain.block_count == block_index:  # Проверяем, можно ли объединить с следующей цепочкой
                        current_chain.block_count += 1
                        break
                    elif current_chain.start_block > block_index:
                        new_chain = FreeBlockChain(block_index, 1)
                        new_chain.next = current_chain
                        if current_chain == self.free_blocks_head:
                            self.free_blocks_head = new_chain
                        else:
                            prev_chain.next = new_chain
                        break

                    prev_chain = current_chain
                    current_chain = current_chain.next


                self.clear_block(block_index)

    def clear_block(self, block_index):
        with open(self.filename, 'r+b') as f:
            f.seek(block_index * self.block_size)
            f.write(b'\x00' * self.block_size)


