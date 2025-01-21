import logging

logging.basicConfig(filename='bot_01.log',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("This is logged to a file.")
