from amiibo import AmiiboDump, AmiiboMasterKey
import random
import sys

class AmiiboCloner:
    def __init__(self, unfixed_info_path, locked_secret_path):
        with open(unfixed_info_path, 'rb') as fp_d, \
                open(locked_secret_path, 'rb') as fp_t:
            self.master_keys = AmiiboMasterKey.from_separate_bin(
                fp_d.read(), fp_t.read())
        self.excluded_values = set([])

    def generate_hex_values(self, num_values=1):
        hex_values = []
        while num_values > 0:
            hex_value = None
            while hex_value is None or hex_value in self.excluded_values:
                hex_value = '04 ' + ' '.join(''.join(random.choice('0123456789ABCDEF') for _ in range(2)) for _ in range(5)) + ' 80'
            hex_values.append(hex_value)
            self.excluded_values.add(hex_value)
            num_values -= 1
        return hex_values

    def exclude_value_from(self, file_path):
        with open(file_path, 'rb') as fp:
            dump = AmiiboDump(self.master_keys, fp.read())
            if dump.uid_hex in self.excluded_values:
                self.excluded_values.add(dump.uid_hex)

    def generate_amiibo_clone(self, input_file, output_file):
        with open(input_file, 'rb') as fp:
            dump = AmiiboDump(self.master_keys, fp.read())
            print('old', dump.uid_hex)
            dump.unlock()
            dump.uid_hex = self.generate_hex_values()[0]
            dump.lock()
            print('new', dump.uid_hex)
            with open(output_file, 'wb') as fp2:
                fp2.write(dump.data)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        amiibo_generator = AmiiboCloner('unfixed-info.bin', 'locked-secret.bin')
        print('input:', input_file)
        print('output:', output_file)
        amiibo_generator.exclude_value_from(input_file)
        amiibo_generator.generate_amiibo_clone(input_file, output_file)
        print('excluded values:', amiibo_generator.excluded_values)
    else:
        print('Usage: python your_script.py input_file output_file')