from roku import Roku
from requests.exceptions import ConnectionError, ConnectTimeout
from socket import gaierror
from configparser import ConfigParser

class InvalidOptionError(Exception):
    pass

#TODO: simplify show_apps method by using built in Roku app object members instead of parsing app list for values
#TODO: add ability to launch apps by name or ID (values displayed by show_apps method)


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
ROKU_APP_OBJ_LEADING_CHARS = "<Application: "
ROKU_APP_OBJ_TRAILING_CHARS = ">"
NO_DEVICES_AUTODISCOVERED_TEXT = "No nearby Roku devices were autodiscovered."
GENERIC_ENTER_VALID_OPTION_PROMPT = "Please enter a valid option."
UNSUCCESSFUL_COMMAND_DIALOGUE = "Could not contact device. Command not sent."
MAX_HEADER_WIDTH = 40
QUARTER_HEADER_WIDTH = int(MAX_HEADER_WIDTH / 4)
HALF_HEADER_WIDTH = int(MAX_HEADER_WIDTH / 2)
THREE_FOURTHS_HEADER_WIDTH = QUARTER_HEADER_WIDTH * 3
CONFIG_FILE = "config.ini"
CONFIG_FILE_CACHED_SECTION = "cached"
RECENT_IP_KEY = "recent_ip"


def welcome():
    print(WELCOME_LOGO)
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


    connection_established = False

    config = ConfigParser()
    config.read(CONFIG_FILE)
    if config.has_section(CONFIG_FILE_CACHED_SECTION):
        ip_addr= config.get(CONFIG_FILE_CACHED_SECTION, RECENT_IP_KEY)
        roku_remote = establish_connection(ip_addr) 

    if not connection_established:
        autodiscovered_devices = Roku.discover()
        if autodiscovered_devices:
            roku_remote = initial_connection_attempt(autodiscovered_devices)
        else: #no devices autodiscovered
            print(NO_DEVICES_AUTODISCOVERED_TEXT)
        
        if connection_established == False:
            roku_remote = establish_connection_loop()

        with open(CONFIG_FILE, "w") as configfile:
            config = ConfigParser()
            config.add_section(CONFIG_FILE_CACHED_SECTION)
            config.set(CONFIG_FILE_CACHED_SECTION, RECENT_IP_KEY, get_ip_from_roku_obj(roku_remote))
            config.write(configfile)

    return roku_remote

def safe_command(roku_command, command_arg = None):
    try:
        if command_arg:
            roku_command(command_arg)
        else:
            roku_command()
        return True
    except (ConnectionError, TimeoutError):
        print(UNSUCCESSFUL_COMMAND_DIALOGUE)
        return False


def parse_app_info(app):
    app = app.removeprefix(ROKU_APP_OBJ_LEADING_CHARS).removesuffix(ROKU_APP_OBJ_TRAILING_CHARS)
    app_id = app.split(maxsplit = 1)[0]
    app_name = (app.split(maxsplit = 1)[1]).rsplit(maxsplit = 1)[0]
    app_version = (app.split(maxsplit = 1)[1]).rsplit(maxsplit = 1)[1]
    return (app_id, app_name, app_version)

def remote_control(roku):

    def show_apps():

        apps_list = roku.apps
        for app in apps_list:
            app = repr(app)
            app_id, app_name, app_version = parse_app_info(app)
            print(f"{app_name.ljust(THREE_FOURTHS_HEADER_WIDTH)} {app_id.ljust(HALF_HEADER_WIDTH)} {app_version.ljust(QUARTER_HEADER_WIDTH)}")
            #print(app)

        input("\nPress ENTER to continue")
        return

    TEXT_LITERAL_COMMAND = "txt"
    prev_command = ""
    COMMANDS_MAP = {
        "b" : {"func" : roku.back,
                "desc" : "Back",
                "args" : False
                },
        "<" : {"func" : roku.channel_down, 
                "desc" : "Channel down",
                "args" : False
                },
        ">" : {"func" : roku.channel_up,
                "desc" : "Channel up",
                "args" : False
                },
        "s" : {"func" : roku.down, 
                "desc" : "Down",
                "args" : False
                },
        #"k": (roku.enter, "Enter"),
        "ff" : {"func" : roku.forward,
                "desc" : "Forward",
                "args" : False
                },
        "h" : {"func" : roku.home,
                "desc" : "Home",
                "args" : False
                },
        "*" : {"func" : roku.info,
                "desc" : "Info",
                "args" : False
                },
        "av1": {"func" : roku.input_av1,
                "desc" : "Source: AV1",
                "args" : False
                },
        "hdmi1" : {"func" : roku.input_hdmi1,
                    "desc" : "Source: HDMI1",
                    "args" : False
                    },
        "hdmi2" : {"func" : roku.input_hdmi2,
                    "desc" : "Source: HDMI2",
                    "args" : False
                    },
        "hdmi3" : {"func" : roku.input_hdmi3,
                    "desc" : "Source: HDMI3",
                    "args" : False
                    },
        "hdmi4" : {"func" : roku.input_hdmi4,
                    "desc" : "Source: HDMI4",
                    "args" : False
                    },
        "tuner" : {"func" : roku.input_tuner,
                    "desc" : "Source: Tuner",
                    "args" : False
                    },
        "a" : {"func" : roku.left,
                "desc" : "Left",
                "args" : False
                },
        TEXT_LITERAL_COMMAND : {"func" : roku.literal,
                                "desc" : "Enter text",
                                "args" : True},
        "p" : {"func" : roku.play,
                "desc" : "Play",
                "args" : False
                },
        "OFF" : {"func" : roku.poweroff,
                "desc" :"Power Off",
                "args" : False
                },
        "on" : {"func" : roku.poweron,
                "desc" : "Power On",
                "args" : False
                },
        "replay" : {"func" : roku.replay,
                    "desc" : "Replay",
                    "args" : False
                    },
        "rew" : {"func" : roku.reverse,
                "desc" : "Reverse",
                "args" : False
                },
        "d" : {"func" : roku.right,
                "desc" : "Right",
                "args" : False
                },
        "search" : {"func" : roku.search,
                    "desc" : "Search",
                    "args" : False
                    },
        "k" : {"func" : roku.select,
                "desc" : "Select",
                "args" : False
                },
        "w" : {"func" : roku.up,
                "desc" : "Up",
                "args" : False
                },
        "-" : {"func" : roku.volume_down,
                "desc" : "Volume -",
                "args" : False
                },
        "+" : {"func" : roku.volume_up,
                "desc" : "Volume +",
                "args" : False
                },
        "m" : {"func" : roku.volume_mute,
                "desc" : "Mute",
                "args" : False
                },
        "apps" : {"func" : show_apps,
                "desc" : "Display available apps",
                "args" : False
                },
        "oa" : {#"func" : launch_app,
                "desc" : "Open app",
                "args" : True
                }
    }

#    def launch_app():
#        return roku[user_app_choice].launch()

    def display_commands():

        def display_commands_header():
            COMMAND_HEADER_TEXT = "COMMAND"
            ACTION_HEADER_TEXT = "ACTION"

            print(f"{ACTION_HEADER_TEXT.center(THREE_FOURTHS_HEADER_WIDTH)}:{COMMAND_HEADER_TEXT.center(QUARTER_HEADER_WIDTH)}")
            print("-" * (MAX_HEADER_WIDTH + 1))
            return

        display_commands_header()

        for (command, properties) in COMMANDS_MAP.items():
            #print(f"{command.ljust(HALF_HEADER_WIDTH)}:{(action[1]).rjust(HALF_HEADER_WIDTH)}")
            print(f"{(properties['desc']).ljust(THREE_FOURTHS_HEADER_WIDTH)}:{command.rjust(QUARTER_HEADER_WIDTH)}")
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

        if (user_command == TEXT_LITERAL_COMMAND):
            command_arg = input("Please enter the text to send to the Roku device: ")
        else:
            command_arg = None
        if safe_command(COMMANDS_MAP[user_command]["func"], command_arg):
            prev_command = user_command

def main():
    welcome()
    try:
        remote_control(initialize_remote())
    except KeyboardInterrupt:
        print("\nExiting. Goodbye.")
    return

if __name__ == "__main__":
    main()
