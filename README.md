This guide assumes that you are using Visual Studio Code.

# Install Depedencies

Open this project in Visual Studio Code
Open a terminal (Ctrl + \`, should be the button to the left of the 1 key)
Run the following commands:

1. `python -m venv westpac_hackathon` (creates a virtual environment for storing dependencies, important on Linux to avoid overwriting older Python packages with newer ones as this can break your operating system/desktop environment)
2. Windows: `source westpac_hackathon/Scripts/activate` | Linux: `source westpac_hackathon/bin/activate` (activates the virtual environment so you can use and install dependencies)
3. `python -m pip install "kivy[full]" kivy_examples tensorflow` (this may take a while)

# Test Project

To test the project, click on the `front_end.py` file and click the play button in the top right. Make sure that the virtual environment is activated (denoted by a `(westpac_hackathon)` prefix). If it is not, run the second command from the Install Dependencies section and try again.

# Notes

Don't worry about warnings from the Tensorflow package. They are just warnings. The tensorflow package for Windows does not have GPU support, meaning that GPU support would require a Linux operating system, most likely through the Windows Subsystem for Linux (WSL) and building of the tensorflow package from scratch for your specific hardware (which I am not expecting anyone to put themselves through).
