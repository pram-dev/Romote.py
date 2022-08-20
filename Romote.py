#adding a comment to test git branches
#adding a second comment

from roku import Roku
from requests.exceptions import ConnectionError, ConnectTimeout
from socket import gaierror

class InvalidOptionError(Exception):
    pass


WELCOME_LOGO = r"""

  ____                       _                        ___   ___   _ 
 |  _ \ ___  _ __ ___   ___ | |_ ___   _ __  _   _   / _ \ / _ \ / |
 | |_) / _ \| '_ ` _ \ / _ \| __/ _ \ | '_ \| | | | | | | | | | || |
 |  _ < (_) | | | | | | (_) | ||  __/_| |_) | |_| | | |_| | |_| || |
 |_| \_\___/|_| |_| |_|\___/ \__\___(_) .__/ \__, |  \___(_)___(_)_|
                                      |_|    |___/                  

"""
ROKU_IP_OBJ_LEADING_CHARS = "<Roku: "
ROKU_IP_OBJ_TRAILING_CHARS = ">"
EMPTY_ROKU_OBJ_IP = "0.0.0.0:8060"
NO_DEVICES_AUTODISCOVERED_TEXT = "No nearby Roku devices were autodiscovered."
GENERIC_ENTER_VALID_OPTION_PROMPT = "Please enter a valid option."
UNSUCCESSFUL_COMMAND_DIALOGUE = "Could not contact device. Command not sent."


def welcome():
    print(WELCOME_LOGO)
    return


def get_roku_ip_strs(devices_list):
    if devices_list: #if devices were discovered and list is not empty
        for device in devices_list:
            device_ip = get_ip_from_roku_obj(device)
    return

def get_ip_from_roku_obj(roku_obj): #turns a singular roku object into an IP string
    return (repr(roku_obj).removeprefix(ROKU_IP_OBJ_LEADING_CHARS).removesuffix(ROKU_IP_OBJ_TRAILING_CHARS).split(":"))[0] #return ip string with unnecessary chars and port number removed, since the default discovered port does not appear to work




def devices_str_list(roku_devices_obj):

    devices_list = []

    for device_obj in roku_devices_obj:
        devices_list.append(get_ip_from_roku_obj(device_obj))

    return devices_list


def basic_connection_check(ip_string):
    print("BASIC_CONNECTION_CHECK. IP_STRING ==", ip_string)
    possible_roku_device = Roku(ip_string)
    possible_roku_device.up()
    return



def autodiscover_choice_prompt(roku_objects_list):


    autodiscovered_devices_strs = devices_str_list(roku_objects_list) #get devices as a list of strings
    total_options = len(roku_objects_list)

    def display_roku_devices():
        for (option_num, ip_str) in zip(range(total_options), autodiscovered_devices_strs):
            print("[" + str(option_num + 1) + "]: <" + ip_str + ">")
        return


    def get_user_device_choice():
        display_roku_devices()
        
        while True:
            user_choice = input("Choose which IP you'd like to connect to and press ENTER: ")

            try:
                if int(user_choice) > 0 and int(user_choice) <= total_options:
                    break
                else:
                    raise InvalidOptionError
            except (ValueError, InvalidOptionError):
                print(GENERIC_ENTER_VALID_OPTION_PROMPT)

        return (int(user_choice) - 1)

    user_choice = get_user_device_choice() #guaranteed to return only recognized/accepted ints as options
    device_ip = autodiscovered_devices_strs[user_choice]

    return device_ip


def initialize_remote():

    connection_established = False

    def establish_connection(device_ip):
        nonlocal connection_established

        try:
            basic_connection_check(device_ip)
            print("Successfully connected to Roku device!")
            established_remote = Roku(device_ip)
            connection_established = True
        except (ConnectionError, ConnectTimeout, gaierror):
            print("Could not establish a connection to this device.")
            established_remote = None
            connection_established = False
            
        return established_remote

    def establish_connection_loop():
        nonlocal connection_established

        while not connection_established:
            user_choice = input("Press ENTER to try to autodiscover nearby Roku devices or enter 'm' and to manually add an IP: ")
            user_choice = user_choice.strip()

            if user_choice == "m" or user_choice == "M": #user chooses to manually enter an IP to connect to
                device_ip = input("Please enter the IP of the device you'd like to connect to, or enter 'a' to autodiscover: ") # get device IP
                if device_ip == "a" or device_ip == "A":
                    autodiscovered_devices = Roku.discover()
                    if not autodiscovered_devices:
                        print(NO_DEVICES_AUTODISCOVERED_TEXT)
                        continue
                    else:
                        device_ip = autodiscover_choice_prompt(autodiscovered_devices)
            elif user_choice == "": #user chooses to try to autodiscover nearby devices
                autodiscovered_devices = Roku.discover()
                print("CURRENTLY IN ELIF BRANCH, TRYING TO REDISCOVER AUTOMATICALLY. CURRENT DISCOVERED:", autodiscovered_devices)
                if not autodiscovered_devices:
                    print(NO_DEVICES_AUTODISCOVERED_TEXT)
                    continue
                else: #some Roku IPs were discovered
                    device_ip = autodiscover_choice_prompt(autodiscovered_devices)
            else: #user enters invalid characters
                print(GENERIC_ENTER_VALID_OPTION_PROMPT)
                continue

            roku_remote = establish_connection(device_ip)        
        return roku_remote

    def initial_connection_attempt(roku_obj_list):
        device_ip = autodiscover_choice_prompt(roku_obj_list)
        roku_remote = establish_connection(device_ip)
        print("CONNECTION_ESTABLISHED ==", connection_established)
        return roku_remote


    autodiscovered_devices = Roku.discover()
    if autodiscovered_devices:
        roku_remote = initial_connection_attempt(autodiscovered_devices)
    else: #no devices autodiscovered
        print(NO_DEVICES_AUTODISCOVERED_TEXT)
    
    if connection_established == False:
        roku_remote = establish_connection_loop()

    return roku_remote

def safe_command(roku_command):
    try:
        roku_command()
        return True
    except (ConnectionError, TimeoutError):
        print(UNSUCCESSFUL_COMMAND_DIALOGUE)
        return False

def remote_control(roku):

    prev_command = ""
    COMMANDS_MAP = {
        "b" : (roku.back, "Back"),
        "<" : (roku.channel_down, "Channel down"),
        ">" : (roku.channel_up, "Channel up"),
        "s" : (roku.down, "Down"),
        #"k": (roku.enter, "Enter"),
        "ff" : (roku.forward, "Forward"),
        "h" : (roku.home, "Home"),
        "*" : (roku.info, "Info"),
        "av1": (roku.input_av1, "Source: AV1"),
        "hdmi1" : (roku.input_hdmi1, "Source: HDMI1"),
        "hdmi2" : (roku.input_hdmi2, "Source: HDMI2"),
        "hdmi3" : (roku.input_hdmi3, "Source: HDMI3"),
        "hdmi4" : (roku.input_hdmi4, "Source: HDMI4"),
        "tuner" : (roku.input_tuner, "Source: Tuner"),
        "w" : (roku.left, "Left"),
        "txt" : (roku.literal, "Enter text"),
        "p" : (roku.play, "Play"),
        "OFF" : (roku.poweroff, "Power Off"),
        "on" : (roku.poweron, "Power On"),
        "replay" : (roku.replay, "Replay"),
        "rew" : (roku.reverse, "Reverse"),
        "d" : (roku.right, "Right"),
        "search" : (roku.search, "Search"),
        "k" : (roku.select, "Select"),
        "w" : (roku.up, "Up"),
        "-" : (roku.volume_down, "Volume -"),
        "+" : (roku.volume_up, "Volume +"),
        "m" : (roku.volume_mute, "Mute")
    }

    def display_commands():
        MAX_HEADER_WIDTH = 40
        HALF_HEADER_WIDTH = int(MAX_HEADER_WIDTH / 2)

        def display_commands_header():
            COMMAND_HEADER_TEXT = "COMMAND"
            ACTION_HEADER_TEXT = "ACTION"


            print(f"{COMMAND_HEADER_TEXT.center(HALF_HEADER_WIDTH)}{ACTION_HEADER_TEXT.center(HALF_HEADER_WIDTH)}")
            print("-" * (MAX_HEADER_WIDTH + 1))
            return




        display_commands_header()

        for (command, action) in COMMANDS_MAP.items():
            print(f"{command.ljust(HALF_HEADER_WIDTH)}:{(action[1]).rjust(HALF_HEADER_WIDTH)}")
        return

    def get_user_command():
        nonlocal prev_command
        user_command = ""

        display_commands()
        print()

        while not (user_command in COMMANDS_MAP):
            if prev_command:
                print(f"Most recent command: [{prev_command}]")
            user_command = input(f"Enter a command and press ENTER or leave blank and ENTER to use most recent command: ")

            if not user_command and prev_command:
                user_command = prev_command

        return user_command

    while True:
        user_command = get_user_command()
        if safe_command(COMMANDS_MAP[user_command][0]):
            prev_command = user_command

    return

def main():
    welcome()
    try:
        remote_control(initialize_remote())
    except KeyboardInterrupt:
        print("\nExiting. Goodbye.")
    return

if __name__ == "__main__":
    main()
