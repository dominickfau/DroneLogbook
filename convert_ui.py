"""Used to convert UI files to Python Code."""

# Code to convert UI files to Python Code from runing "Convert UI Files to Python" task
import optparse
import os
import sys

# Valid command line arguments: --input=<input_folder> --output=<output_folder>
# Parse command line arguments
parser = optparse.OptionParser()
parser.add_option('--input', dest='input', help='Input folder')
parser.add_option('--output', dest='output', help='Output folder')

opts, args = parser.parse_args()

# Check if input and output folders are valid
if not os.path.isdir(opts.input):
    print('Input folder is not valid')
    sys.exit(1)

if not os.path.isdir(opts.output):
    print('Output folder is not valid')
    sys.exit(1)

# Get all .ui files in input folder
ui_files = []
for root, dirs, files in os.walk(opts.input):
    for file in files:
        if file.endswith('.ui'):
            ui_files.append(os.path.join(root, file))

# Convert each .ui file to .py file
for ui_file in ui_files:
    print(f"Converting {ui_file}")
    py_file = os.path.join(opts.output, os.path.basename(ui_file).replace('.ui', '.py'))
    command_ = f"pyuic5 {ui_file} -o {py_file}"
    os.system(command_)

    with open(py_file, 'r') as f:
        lines = f.readlines()

    with open(py_file, 'w') as f:
        for line in lines:
            if line.__contains__('class Ui_MainWindow(object)'):
                line = line.replace('class Ui_MainWindow(object)', 'class Ui_MainWindow(QtWidgets.QMainWindow)')
            elif line.__contains__('QtCore.QMetaObject.connectSlotsByName(MainWindow)'):
                line = line.replace('QtCore.QMetaObject.connectSlotsByName(MainWindow)', '')
            
            f.write(line)