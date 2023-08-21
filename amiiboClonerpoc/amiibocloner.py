from amiibo import AmiiboDump, AmiiboMasterKey
import sys
import random

excluded_values = set([])  # Initial excluded values

def generate_hex_values(excluded_values, num_values=1):
    hex_values = []
    while num_values > 0:
        hex_value = None
        while hex_value is None or hex_value in excluded_values:
            hex_value = '04 '+' '.join(''.join(random.choice('0123456789ABCDEF') for _ in range(2)) for _ in range(5)) + ' 80'
        hex_values.append(hex_value)
        excluded_values.add(hex_value)
        num_values -= 1
    return hex_values

def exclude_value_from(filePath):
    global excluded_values
    with open('unfixed-info.bin', 'rb') as fp_d, \
            open('locked-secret.bin', 'rb') as fp_t:
        master_keys = AmiiboMasterKey.from_separate_bin(
            fp_d.read(), fp_t.read())
        with open(filePath, 'rb') as fp:
            dump = AmiiboDump(master_keys, fp.read())
            excluded_values.add(dump.uid_hex)

def generate_amiibo_Clon(filePath, outputFile):
    global excluded_values
    with open('unfixed-info.bin', 'rb') as fp_d, \
            open('locked-secret.bin', 'rb') as fp_t:
        master_keys = AmiiboMasterKey.from_separate_bin(
            fp_d.read(), fp_t.read())
        with open(filePath, 'rb') as fp:
            dump = AmiiboDump(master_keys, fp.read())
            print('old', dump.uid_hex)
            dump.unlock()
            dump.uid_hex = generate_hex_values(excluded_values)[0]
            dump.lock()
            #dump.unset_lock_bytes()
            print('new', dump.uid_hex)
            with open(outputFile, 'wb') as fp2:
                fp2.write(dump.data)

if __name__ == '__main__':
    inputFile = None
    outputFile = None
    for arg in sys.argv:
        if '-in=' in arg:
            inputFile = str(arg).split('-in=')[-1]
        if '-out=' in arg:
            outputFile = str(arg).split('-out=')[-1]
    if inputFile!=None and outputFile!=None:
        print('input: '+inputFile)
        print('output: '+outputFile)
        exclude_value_from(inputFile)
        generate_amiibo_Clon(inputFile,outputFile)
        print('excluded vqlues', excluded_values)
    else:
        print('input and output undefined')
