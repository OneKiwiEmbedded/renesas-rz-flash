# rzv-flash

- `./flash.py --spi`
- `./flash.py --mmc`

### QSPI RZ/G2L RZ/G2LC RZ/G2UL RZ/V2L
| File name | Address to load to RAM | Address to save to ROM |
|---|:---:|:---:|
| bl2_name.srec | 11E00 | 00000 |
| fip-name.srec | 00000 | 1D200 |


### eMMC RZ/G2L RZ/G2LC RZ/G2UL RZ/V2L
| File name | Partition to save to eMMC | Address to save to eMMC | Address to load to RAM |
|---|:---:|:---:|:---:|
| bl2_name.srec | 1 | 00000001 | 11E00 |
| fip-name.srec | 1 | 00000100 | 00000 |
