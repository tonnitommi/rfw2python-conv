import subprocess
from RPA.Robocorp.Vault import Vault
from RPA.OpenAI import OpenAI
from RPA.FileSystem import FileSystem

vault = Vault()
openai = OpenAI()
filesystem = FileSystem()

secrets = vault.get_secret("OpenAI")
openai.authorize_to_openai(api_key=secrets["key"])

prompt_template_convert = """
Your are a software engineer who is tasked to convert Robot Framework robots to python.
Use rpaframework libraries and keywords when they are available, and convert keywords in
to individual python methods. Pay attention following the snake case in Python. Also pay
attention to rpaframework method names. They are represented with Capital letters in the
Robot Framework code, but in python they are all lower case with snake case. For example
Find Text becomes find_text.

Reply only with code, do not ever add any extra text to your reply!

Here are some examples of a successfull conversion.

EXAMPLE 1:

Original Robot Framework code:
*** Settings ***
Library    RPA.Tables
Library    RPA.Excel.Files

*** Keywords ***
Read orders as table
    Open workbook    ${ORDERS_FILE}
    ${worksheet}=    Read worksheet   header=${TRUE}
    ${orders}=       Create table     ${worksheet}
    [Return]         ${orders}
    [Teardown]       Close workbook

Converted python code:
from RPA.Excel.Files import Files

def read_excel_worksheet(path, worksheet):
    lib = Files()
    lib.open_workbook(path)
    try:
        return lib.read_worksheet(worksheet)
    finally:
        lib.close_workbook()

if __name__ == "__main__":
    orders = read_excel_worksheet("orders.xlsx", "orders")

EXAMPLE 2:

Original Robot Framework code:
*** Settings ***
Library    RPA.PDF
Library    String

*** Tasks ***
Extract Data From First Page
    ${text} =    Get Text From PDF    report.pdf
    ${lines} =     Get Lines Matching Regexp    ${text}[${1}]    .+pain.+
    Log    ${lines}

Get Invoice Number
    Open Pdf    invoice.pdf
    ${matches} =  Find Text    Invoice Number
    Log List      ${matches}

Fill Form Fields
    Switch To Pdf    form.pdf
    ${fields} =     Get Input Fields   encoding=utf-16
    Log Dictionary    ${fields}
    Set Field Value    Given Name Text Box    Mark
    Save Field Values    output_path=${OUTPUT_DIR}${/}completed-form.pdf
    ...                  use_appearances_writer=${True}

Converted python code:
from RPA.PDF import PDF
from robot.libraries.String import String

pdf = PDF()
string = String()

def extract_data_from_first_page():
    text = pdf.get_text_from_pdf("report.pdf")
    lines = string.get_lines_matching_regexp(text[1], ".+pain.+")
    print(lines)

def get_invoice_number():
    pdf.open_pdf("invoice.pdf")
    matches = pdf.find_text("Invoice Number")
    for match in matches:
        print(match)

def fill_form_fields():
    pdf.switch_to_pdf("form.pdf")
    fields = pdf.get_input_fields(encoding="utf-16")
    for key, value in fields.items():
        print(f"{key}: {value}")
    pdf.set_field_value("Given Name Text Box", "Mark")
    pdf.save_field_values(
        output_path="completed-form.pdf",
        use_appearances_writer=True
    )

if __name__ == "__main__":
    extract_data_from_first_page()
    get_invoice_number()
    fill_form_fields()

Below is the code you need to convert to python. Remember, do not add anything else than the code to your reply.

$code_to_convert
"""

prompt_template_fix = """
The code you provided do not run without errors. PLease look at the error below, and fix the code.
Only reply with the fixed code, no other text please. No apologies or anything pointing out the
issues. Just the code.

$code_to_fix
"""

def convert_a_bot(code): 
    prompt = prompt_template_convert
    prompt = prompt.replace("$code_to_convert", code)
    
    response, conversation = openai.chat_completion_create(
        user_content=prompt
    )
    return response, conversation

def get_some_code():
    matches = filesystem.find_files("code/*.robot")
    return filesystem.read_file(matches[0]), matches[0]

def create_new_file(path, code):
    filesystem.create_file(path=path, content=code, overwrite=True)

def fix_a_bot(error, conversation):
    prompt = prompt_template_fix
    prompt = prompt.replace("$code_to_fix", error)

    response, conversation = openai.chat_completion_create(
        conversation=[conversation],
        user_content=prompt
    )
    return response, conversation

if __name__ == "__main__":
    new_path = "code/converted.py"

    # first conversion
    code_str, path = get_some_code()
    print(f"RUN #1: Conversion starting")
    new_code, conversation = convert_a_bot(code_str)
    create_new_file(new_path, new_code)
    print(f"RUN #1: Conversion completeled")
    
    # first run
    print(f"RUN #1: Test run starting")
    result = subprocess.run(["python", "code/converted.py"], capture_output=True, text=True)
    print(f"RUN #1: Test run completed with result: {result.returncode}")

    # try fixing
    if result.returncode != 0:
        
        print(f"RUN #1: ERROR WAS: {result.stderr}")

        for i in range(2):
            print(f"RUN #{i+2}: Trying to fix the code")
            fixed_code, conversation = fix_a_bot(result.stderr, conversation)
            create_new_file(new_path, fixed_code)
            print(f"RUN #{i+2}: Code fixes completed")

            print(f"RUN #{i+2}: Test run starting")
            result = subprocess.run(["python", "code/converted.py"], capture_output=True, text=True)
            print(f"RUN #{i+2}: Test run completed with result: {result.returncode}")

            if result.returncode == 0:
                print(f"RUN #{i+2}: COMPLETED SUCCESSFULLY")
                break
            else:
                print(f"RUN #{i+2}: ERROR WAS: {result.stderr}")

        print("CONVERSION FAILED")

    else:
        print("RUN #1: COMPLETED SUCCESSFULLY")