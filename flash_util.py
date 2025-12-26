#!/usr/bin/python3

import os
import sys
import serial
import platform
import argparse
import subprocess
from alive_progress import alive_bar

FLASH_WRITER = "Flash_Writer_SCIF_RZV2H_DEV_INTERNAL_MEMORY.mot"

BL2_SPI_8GB_FILE = "bl2_bp_spi-onekiwi-rzv2h-8gb.srec"
BL2_MMC_8GB_FILE = "bl2_bp_emmc-onekiwi-rzv2h-8gb.srec"
FIP_8GB_FILE = "fip-onekiwi-rzv2h-8gb.srec"

BL2_SPI_16GB_FILE = "bl2_bp_spi-onekiwi-rzv2h-16gb.srec"
BL2_MMC_16GB_FILE = "bl2_bp_emmc-onekiwi-rzv2h-16gb.srec"
FIP_16GB_FILE = "fip-onekiwi-rzv2h-16gb.srec"

TIME = 100000000

FLASH_QSPI = 1
FLASH_EMMC = 2
RAM_TEST = 3

BOARD_8GB = 1
BOARD_16GB = 2

class FlashUtil:
    def __init__(self):
        self.flash_type = 0
        self.board = 0
        self.mpu = 0
        self.serial = ''
        self.flash_writer_image = FLASH_WRITER
        self.total = 0

        if self.flash_type == FLASH_EMMC:
            if self.board == BOARD_8GB:
                self.bl2_image = BL2_MMC_8GB_FILE
            if self.board == BOARD_16GB:
                self.bl2_image = BL2_MMC_16GB_FILE

        argparser = self.argparse_defaults()
        self.handle_path_overrides()

        if self.flash_type == 0 or self.board == 0:
            print("Utility to flash OneKiwi RZV2L RZV2N RZV2H")
            print("Example:")
            print("    ./flash.py --spi --8gb")
            print("    ./flash.py --spi --16gb")
            #print("    ./flash.py --mmc --8gb")
            #print("    ./flash.py --mmc --16gb")
            return
        
        self.setup_serial_port()
        self.write_bootloader()
    
    def argparse_defaults(self):
        argparser = argparse.ArgumentParser(
            description="Utility to flash OneKiwi RZV2L RZV2N RZV2H.\n",
            epilog="Example:\n\t./flash.py --spi",
        )

        # Add arguments
        # Commands
        # Serial port arguments
        argparser.add_argument(
            "--8gb",
            dest="board8gb",
            action="store_true",
            help="Board 8GB.",
        )
        argparser.add_argument(
            "--16gb",
            dest="board16gb",
            action="store_true",
            help="Board 16GB.",
        )
        argparser.add_argument(
            "--spi",
            dest="flashQSPI",
            action="store_true",
            help="Flash to QSPI.",
        )
        argparser.add_argument(
            "--mmc",
            dest="flashEMMC",
            action="store_true",
            help="Flash to eMMC.",
        )
        argparser.add_argument(
            "--ram",
            dest="ramTest",
            action="store_true",
            help="Flash to eMMC.",
        )
        argparser.add_argument(
            "--serial_port",
            default="/dev/ttyUSB0",
            dest="serialPort",
            action="store",
            help="Serial port used to talk to board (defaults to: /dev/ttyUSB0).",
        )
        argparser.add_argument(
            "--serial_port_baud",
            default=115200,
            dest="baudRate",
            action="store",
            type=int,
            help="Baud rate for serial port (defaults to: 115200).",
        )

        self.args = argparser.parse_args()
        return argparser
    
    def handle_path_overrides(self):
        if self.args.serialPort:
            self.serial = self.args.serialPort
        if self.args.flashEMMC:
            self.flash_type = FLASH_EMMC
            self.total = 4
        if self.args.flashQSPI:
            self.flash_type = FLASH_QSPI
            self.total = 3
        if self.args.ramTest:
            self.flash_type = RAM_TEST
            self.total = 2
        if self.args.board8gb:
            self.board = BOARD_8GB
            self.bl2_image = BL2_SPI_8GB_FILE
            self.fip_image = FIP_8GB_FILE
        if self.args.board16gb:
            self.board = BOARD_16GB
            self.bl2_image = BL2_SPI_16GB_FILE
            self.fip_image = FIP_16GB_FILE

    def setup_serial_port(self):
        try:
            if platform.system() == 'Linux':
                subprocess.run(["sudo", "chmod", "777", self.serial])
            self.serial_port = serial.Serial(self.serial, 115200)
        except Exception as e:
            print("Error:: ", e)

    def get_size(self, path):
        size = os.path.getsize(path)
        if size < 1024:
            return f"{size} bytes"
        elif size < pow(1024,2):
            return f"{round(size/1024, 2)} KB"
        elif size < pow(1024,3):
            return f"{round(size/(pow(1024,2)), 2)} MB"
        elif size < pow(1024,4):
            return f"{round(size/(pow(1024,3)), 2)} GB"
    
    # Function to write bootloader
    def write_bootloader(self):
        with alive_bar(self.total, title='Flashing', bar='halloween', spinner='notes', enrich_print=False) as bar:
            self.check_bootloader_files()
            self.flash_flash_writer(bar)
            self.change_baudrate()
            bar()

            if self.flash_type == FLASH_QSPI:
                #self.flash_erase_qspi(bar)
                self.flash_bl2_image_qspi(bar)
                bar()
                
                self.flash_fip_image_qspi(bar)
                bar()

            if self.flash_type == FLASH_EMMC:
                #self.flash_erase_emmc()
                self.setup_emmc_flash(bar)
                bar()

                self.flash_bl2_image_emmc(bar)
                bar()
                
                self.flash_fip_image_emmc(bar)
                bar()
            
            if self.flash_type == RAM_TEST:
                self.write_serial_cmd("DDRCK")
                self.wait_for_serial_read(">")
                self.write_serial_cmd("RAMCK")
                self.wait_for_serial_read(">")
                bar()

            self.serial_port.close()
            print("Done flashing bootloader!")

    def change_baudrate(self):
        self.write_serial_cmd("SUP")
        self.wait_for_serial_read("the terminal.")
        self.serial_port.baudrate = 921600

    def flash_flash_writer(self, bar):
        bar.text = 'Please power on board. Make sure the board to SCIF Download mode.'

        self.wait_for_serial_read("SRAM ---------------")
        size = self.get_size(self.flash_writer_image)
        if self.flash_type == FLASH_QSPI:
            bar.text = 'QSPI Flashing: ' + self.flash_writer_image + ' (' + size + ')'
        elif self.flash_type == FLASH_EMMC:
            bar.text = 'eMMC Flashing: ' + self.flash_writer_image + ' (' + size + ')'
        else:
            bar.text = 'RAM Test: ' + self.flash_writer_image + ' (' + size + ')'
        self.write_file_to_serial(self.flash_writer_image)
        self.wait_for_serial_read(">")

    def flash_erase_qspi(self, bar):
        bar.text = 'Erase QSPI'

        self.write_serial_cmd("XCS")
        #self.write_serial_cmd("XCS", prefix="\r")
        self.wait_for_serial_read("(y/n)")
        self.write_serial_cmd("y")
        self.write_serial_cmd("y")
        self.wait_for_serial_read(">")

    def flash_bl2_image_qspi(self, bar):
        size = self.get_size(self.bl2_image)
        bar.text = 'QSPI Flashing: ' + self.bl2_image + ' (' + size + ')'

        self.write_serial_cmd("XLS2")

        self.wait_for_serial_read("Please Input : H'")
        self.write_serial_cmd("8101E00")

        self.wait_for_serial_read("Please Input : H'")
        self.write_serial_cmd("00000")

        self.wait_for_serial_read("stop load)")

        self.write_file_to_serial(self.bl2_image)
        self.wait_for_serial_read(">")

    def flash_fip_image_qspi(self, bar):
        size = self.get_size(self.fip_image)
        bar.text = 'QSPI Flashing: ' + self.fip_image + ' (' + size + ')'

        self.write_serial_cmd("XLS2")

        self.wait_for_serial_read("Please Input : H'")
        self.write_serial_cmd("00000")

        self.wait_for_serial_read("Please Input : H'")
        self.write_serial_cmd("60000")

        self.wait_for_serial_read("stop load)")

        self.write_file_to_serial(self.fip_image)
        self.wait_for_serial_read(">")

    def flash_bootloader_qspi(self):
        self.flash_erase_qspi()
        self.flash_bl2_image_qspi()
        self.flash_fip_image_qspi()

    def flash_erase_emmc(self, bar):
        bar.text = 'Erase eMMC'

        self.write_serial_cmd("EM_E")
        self.wait_for_serial_read(">")
        self.write_serial_cmd("1")
        self.wait_for_serial_read(">")

    def setup_emmc_flash(self, bar):
        bar.text = 'Setup eMMC'

        self.write_serial_cmd("EM_SECSD")
        self.wait_for_serial_read(":")
        self.write_serial_cmd("b1")
        self.wait_for_serial_read(":")
        self.write_serial_cmd("2")
        self.wait_for_serial_read(">")
        self.write_serial_cmd("EM_SECSD")
        self.wait_for_serial_read(":")
        self.write_serial_cmd("b3")
        self.wait_for_serial_read(":")
        self.write_serial_cmd("8")
        self.wait_for_serial_read(">")

    def flash_bl2_image_emmc(self, bar):
        size = self.get_size(self.bl2_image)
        bar.text = 'eMMC Flashing: ' + self.bl2_image + ' (' + size + ')'

        self.write_serial_cmd("EM_W")

        self.wait_for_serial_read(">")
        self.write_serial_cmd("1")
        self.wait_for_serial_read(":")
        self.write_serial_cmd("1")
        self.wait_for_serial_read(": ")
        self.write_serial_cmd("8101E00")

        self.wait_for_serial_read("stop load)")
        self.write_file_to_serial(self.bl2_image)
        self.wait_for_serial_read(">")

    def flash_fip_image_emmc(self, bar):
        size = self.get_size(self.fip_image)
        bar.text = 'eMMC Flashing: ' + self.fip_image + ' (' + size + ')'

        self.write_serial_cmd("EM_W")

        self.wait_for_serial_read(")>")
        self.write_serial_cmd("1")
        self.wait_for_serial_read(":")
        self.write_serial_cmd("300")
        self.wait_for_serial_read(": ")
        self.write_serial_cmd("44000000")

        self.wait_for_serial_read("stop load)")
        self.write_file_to_serial(self.fip_image)
        self.wait_for_serial_read(">")

    def flash_bootloader_emmc(self):
        self.flash_erase_emmc()
        self.setup_emmc_flash()
        self.flash_bl2_image_emmc()
        self.flash_fip_image_emmc()

    def check_bootloader_files(self):
        if not os.path.isfile(self.flash_writer_image):
            die(f"Missing flash writer image: {self.flash_writer_image}")

        if not os.path.isfile(self.bl2_image):
            die(f"Missing bl2 image: {self.bl2_image}")

        if not os.path.isfile(self.fip_image):
            die(f"Missing FIP image: {self.fip_image}")

    def write_serial_cmd(self, cmd, prefix=""):
        """
        Writes a command to the serial port.

        Args:
            cmd (str): The command to write to the serial port.
            prefix (str): What to prepend before the command. Useful for prepending
                carriage returns.
        """
        self.serial_port.write(f"{prefix}{cmd}\r".encode())

    # Function to write file over serial
    def write_file_to_serial(self, file):
        """
        Writes the contents of a file to the serial port.

        Args:
            file (str): The path to the file to be written.

        Returns:
            None
        """
        with open(file, "rb") as transmit_file:
            self.serial_port.write(transmit_file.read())
            transmit_file.close()

    def wait_for_serial_read(self, cond="\n"):
        """
        Reads data from the serial port until the specified condition is met.

        Args:
            cond (str): The condition to wait for before returning the data.
                Defaults to newline character.
            print_buffer (bool): Whether to print the read data to the console. Defaults to False.

        Returns:
            bytes: The data read from the serial port.
        """
        buf = self.serial_port.read_until(cond.encode())

        print(f"{buf.decode()}")

        return buf

def die(msg="", code=1):
    """
    Prints an error message and exits the program with the given exit code.
    """
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)