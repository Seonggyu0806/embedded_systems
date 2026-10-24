import board
import busio
import adafruit_ssd1306

OLED_ADDR = 0x3C

i2c = busio.I2C(board.SCL, board.SDA)
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=OLED_ADDR)

display.fill(0)
display.text("Seonggyu", 0, 0, 1)
display.text("Embedded System", 0, 16, 1)
display.text("I2C OLED", 0, 32, 1)
display.text(f"addr: {hex(OLED_ADDR)}", 0, 48, 1)
display.show()

print("OLED 표시 완료")
