import xml.etree.ElementTree as ET
import subprocess
import shlex
import os
import sys
import importlib.util

class XMLCApp:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.variables = {}

    def run(self):
        self._handle_node(self.root)

    def _handle_node(self, node):
        if node.tag == 'app':
            for child in node:
                self._handle_node(child)

        elif node.tag == 'menu':
            self._handle_menu(node)

        elif node.tag == 'text':
            text_content = node.text.strip() if node.text else ''
            print(text_content)

        elif node.tag == 'input':
            prompt = node.attrib.get('prompt', 'Enter input:')
            val = input(f"{prompt} ")
            varname = node.attrib.get('var', '')
            if varname:
                setattr(self, varname, val)
                self.variables[varname] = val

        elif node.tag == 'action':
            self._handle_action(node)

        elif node.tag == 'python':
            self._handle_python(node)

    def _handle_menu(self, menu_node):
        title = menu_node.attrib.get('title', 'Menu')
        print(f"\n=== {title} ===")
        options = menu_node.findall('option')

        for idx, opt in enumerate(options):
            label = opt.attrib.get('label', f"Option {idx + 1}")
            print(f"{idx + 1}. {label}")

        choice = input("Choose an option: ")
        try:
            selected = options[int(choice) - 1]
            for child in selected:
                self._handle_node(child)
        except (IndexError, ValueError):
            print("Invalid selection.")

    def _handle_action(self, action_node):
        script = action_node.attrib.get("script")
        args = action_node.attrib.get("args", "")

        if not script:
            print("[ERROR] <action> tag missing 'script' attribute.")
            return

        script_path = os.path.abspath(script)
        if not os.path.exists(script_path):
            print(f"[ERROR] Script not found: {script_path}")
            return

        try:
            print(f"[INFO] Running script: {script_path}")
            result = subprocess.run(
                ["python", script_path] + shlex.split(args),
                capture_output=True,
                text=True
            )
            print("[OUTPUT]")
            print(result.stdout)
            if result.stderr:
                print("[ERROR OUTPUT]")
                print(result.stderr)
        except Exception as e:
            print(f"[EXCEPTION] Failed to run script: {e}")

    def _handle_python(self, python_node):
        code = python_node.text
        if code:
            try:
                exec(code, {"self": self})
            except Exception as e:
                print(f"[PYTHON ERROR] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python xmlc.py <app.xml> or python xmlc.py <script.py>")
        input("Press Enter to exit...")
        sys.exit(1)

    path = sys.argv[1]
    print(f"[DEBUG] Running xmlc with argument: {path}")

    if path.endswith(".xml"):
        app = XMLCApp(path)
        app.run()

    elif path.endswith(".py"):
        script_path = os.path.abspath(path)
        if not os.path.exists(script_path):
            print(f"[ERROR] Script file not found: {script_path}")
            input("Press Enter to exit...")
            sys.exit(1)

        spec = importlib.util.spec_from_file_location("user_script", script_path)
        user_script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_script)

        if hasattr(user_script, "main") and callable(user_script.main):
            user_script.main()
        else:
            print(f"[WARNING] The script {path} has no callable main() function.")
    else:
        print("Unsupported file type. Use .xml for XML app or .py for Python script.")
    
    print("[DEBUG] Finished running.")
    input("Press Enter to exit...")

