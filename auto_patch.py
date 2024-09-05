# Simple python script to auto generate an update / compatibility patch.
# If you don't do this, you may lose resources or buildings for nomad empires.

import os



# Get building names
def get_building_names(buildings_path):
    building_list = []

    # If we can't find it, assume there's nothing we need.
    try:
        for file in os.listdir(buildings_path):
            if os.path.isfile(os.path.join(buildings_path, file)):
                f = open(buildings_path+file, 'r')
                # We only assume lines at this level are building definitions
                indent_level = 0
                for line in f:
                    # Remove all whitespace
                    line = line.strip()
                    line = line.replace(' ', '')
                    if line != '': # ignore empty lines
                        if line[0] != '#' and line[0] != '@': # ignore comments and variables
                            if indent_level == 0:
                                line = line.split('#')[0] # ignore inline comments
                                building_list.append(line[:-2])
                                #print(line[:-2]) # watch out for holdings if not wanted
                            if '={' in line:
                                indent_level +=1
                            if '}' in line:
                                indent_level -=1
    except:
        pass
    return building_list

def get_resource_list(resource_path, ignore_list=['time']):
    resource_list = []

    # If we can't find it, assume there's nothing we need.
    try:
        # Get all stellaris resources
        for file in os.listdir(resource_path):
            if os.path.isfile(os.path.join(resource_path, file)):
                f = open(resource_path+file, 'r')
                # We only assume lines at this level are resource definitions
                indent_level = 0
                for line in f:
                    # Remove all whitespace
                    line = line.strip()
                    line = line.replace(' ', '')
                    if line != '': # ignore empty lines
                        if line[0] != '#' and line[0] != '@': # ignore comments and variables
                            if indent_level == 0:
                                if line[:-2] not in ignore_list:
                                    resource_list.append(line[:-2])
                            if '={' in line:
                                indent_level +=1
                            if '}' in line:
                                indent_level -=1
    except:
        pass
    return resource_list

# main

output_directory = input('Please input an output directory for the patch files:')                         
stellaris_directory = input('Please input your Stellaris install location:')
install_directories = [stellaris_directory]

finished = False
while not finished:
    modded_input = input('Please enter the install location of any mods you want to add compatibility for. Type "a" to finish:')
    if modded_input.lower() == 'a':
        finished = True
    else:
        install_directories.append(modded_input)


all_buildings_list = set()
all_resources_list = set()
for location in install_directories:
    location = location.replace('\\', '/')

    # Buildings
    building_path = location + f'/common/buildings/'
    for entry in (get_building_names(building_path)):
        all_buildings_list.add(entry)

    # Resources
    resource_path = location + f'/common/strategic_resources/'
    for entry in (get_resource_list(resource_path)):
        all_resources_list.add(entry)

# Process results

load_building_entries = []
save_building_entries = []

resource_modifier_entries = []
resource_encoding_stockpile_entries = 'nmod_encode_all_resources = {' # Wrapper overwrite
resource_decoding_stockpile_entries = 'nmod_decode_all_resources = {' # Wrapper overwrite
resource_encoding_resource_income = '''
nmod_encode_all_resource_incomes = {
    $TARGET$ = {
        save_event_target_as = nmod_arkship_target_to_save_resource_income_to
    }
'''# Wrapper overwrite
resource_refresh_income_entries = 'nmod_refresh_all_resource_income_modifiers = {' # Wrapper overwrite

# Buildings
for entry in all_buildings_list:
    save_building_entries.append('nmod_save_building_count = { TARGET = fromfrom BUILDING = ' + entry + ' }')
    load_building_entries.append('nmod_load_building_count = { TARGET = fromfrom BUILDING = ' + entry + ' }')

# Resources
sorted_list = []
for element in all_resources_list:
    sorted_list.append(element)

sorted_list.sort()
for element in sorted_list:
    resource_modifier_entries.append('nmod_arkship_'+element+'_income = {'+'\n\t'+'country_base_'+element+'_produces_add = 1'+'\n\t'+'hide_from_country_list = yes'+'\n'+'}')
    resource_encoding_stockpile_entries = resource_encoding_stockpile_entries + '\n\t' + 'nmod_encode_resource = { RESOURCE = '+element+' }'
    resource_decoding_stockpile_entries = resource_decoding_stockpile_entries + '\n\t' + 'nmod_decode_resource = { RESOURCE = '+element+' }'
    resource_encoding_resource_income = resource_encoding_resource_income + '\n\t' + 'nmod_encode_resource_income = { RESOURCE = '+element+' }'


resource_encoding_stockpile_entries = resource_encoding_stockpile_entries + '\n}'
resource_decoding_stockpile_entries = resource_decoding_stockpile_entries + '\n}'
resource_encoding_resource_income = resource_encoding_resource_income + '''

    # Set display values for resources that will be shown collectively
    $TARGET$ = {  nmod_set_display_values = yes }
}
'''

os.makedirs(output_directory + '/common/scripted_effects')
os.makedirs(output_directory + '/common/static_modifiers')

misc_effects_uri = output_directory + '/common/scripted_effects/zzz_nmod_compatch_misc_effects.txt' # LIOS
resource_modifiers_uri = output_directory + '/common/static_modifiers/~~nmod_compatch_resource_income_modifiers.txt' # FIOS
buildings_effects_uri = output_directory + '/common/scripted_effects/zzz_nmod_compatch_building_effects.txt' # LIOS

misc_effects_file = open(misc_effects_uri, "x")
misc_effects_file.write(resource_encoding_stockpile_entries + '\n')
misc_effects_file.write(resource_decoding_stockpile_entries + '\n')
misc_effects_file.write(resource_encoding_resource_income + '\n')
misc_effects_file.close()


resource_modifiers_file = open(resource_modifiers_uri, "x")
for entry in resource_modifier_entries:
    resource_modifiers_file.write(entry)
resource_modifiers_file.close()
    
buildings_effects_file = open(buildings_effects_uri, "x")

buildings_effects_file.write('# Saving buildings \n')
buildings_effects_file.write('''
# from = planet
# fromfrom = arkship fleet
nmod_save_buildings_wrapper = {
    # Save the temp variable
    export_trigger_value_to_variable = {
        trigger = num_buildings
        parameters = { type = any }
        variable = nmod_temp_building_count_display_value
    }
    fromfrom = {
        set_variable = {
            which = nmod_building_count_display_value
            value = prev.nmod_temp_building_count_display_value
        }
    }''')

for entry in save_building_entries:
    buildings_effects_file.write('\n\t' + entry)
buildings_effects_file.write('\n}')
                             
buildings_effects_file.write('\n# Loading \n')
buildings_effects_file.write('''
# from = arkship fleet
# fromfrom = target planet
nmod_load_building_wrapper = {''')

for entry in load_building_entries:
    buildings_effects_file.write('\n\t' + entry)                      
buildings_effects_file.write('\n}')
buildings_effects_file.close()
