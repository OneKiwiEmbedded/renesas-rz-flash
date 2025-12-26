# rzv-flash

- `./flash.py --spi --8gb`
- `./flash.py --spi --16gb`

### xSPI RZ/V2H
| File name | Address to load to RAM | Address to save to ROM |
|---|:---:|:---:|
| bl2_name.srec | 8101E00 | 00000 |
| fip-name.srec | 00000 | 60000 |


### eMMC RZ/V2H
| File name | Partition to save to eMMC | Address to save to eMMC | Address to load to RAM |
|---|:---:|:---:|:---:|
| bl2_name.srec | 1 | 00000001 | 8101E00 |
| fip-name.srec | 1 | 00000300 | 44000000 |
