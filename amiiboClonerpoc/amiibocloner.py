from amiibo import AmiiboDump, AmiiboMasterKey
with open('unfixed-info.bin', 'rb') as fp_d, \
        open('locked-secret.bin', 'rb') as fp_t:
    master_keys = AmiiboMasterKey.from_separate_bin(
        fp_d.read(), fp_t.read())

with open('Link_Link_Awakening.bin', 'rb') as fp:
    dump = AmiiboDump(master_keys, fp.read())
    print('old', dump.uid_hex)
    dump.unlock()
    dump.uid_hex = '04 FA FB FC FD FF F1'
    dump.lock()
    #dump.unset_lock_bytes()
    print('new', dump.uid_hex)
    with open('Link_Link_Awakening_clone.bin', 'wb') as fp2:
        fp2.write(dump.data)