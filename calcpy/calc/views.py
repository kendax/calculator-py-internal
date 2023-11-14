'''
Holds the logic for the calculator
'''
import re

from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

# Define a dictionary holding the calculator operators, each assigned an
# integer indicating its precedence
precedence = {"+": 1, "-": 1, "*": 2, "/": 2, "*-": 3}

def is_operator(token):
    """Function to check if a string is an operator or a negative sign"""
    return token in precedence or (token == "-" and len(token) == 1)


def is_special_character(c):
    """Function to check if a character is an operator"""
    operators = "([*\\-+*/()])"
    return c in operators


def parse_number(token):
    """Function to parse a number from a string to a float"""
    value = float(token)
    return value


def add_whitespace_around_operators(input_string):
    """Function to add whitespace around operators in a string"""
    # Define a regular expression pattern to match operators
    pattern = r"([*\-+*/()])"

    try:
        # Compile the regular expression
        regex = re.compile(pattern)

        # Use the regular expression to find matches and add whitespace around
        # them
        result = re.sub(regex, r" \1 ", input_string)
        return result
    except re.error as e:
        print("Error compiling regular expression:", e)
        return input_string


def get_input_as_string(values):
    """Function to concatenate values from a list into a single string"""
    result = "".join(values)
    return result

def contains_special_characters(string):
    """Function to check if a string contains any operator"""
    # Define a regular expression pattern to match operators
    pattern = r"([*\-+*/()])"  # This matches any operators

    # Use re.search to check if the string contains any operators
    return bool(re.search(pattern, string))


def found_operator_func(lst):
    """Function to check if the elements of a list contain an operator"""
    for item in lst:
        if contains_special_characters(item):
            return True
    return False


def period_in_input_func(lst):
    """Function to check if any element of a list is a period"""
    for item in lst:
        if "." in item:
            return True
    return False

def period_in_last_operand(input_list):
    """Check whether there is a period in the last number occurring after an operator"""
    last_operator_index = -1

    # Find the index of the last operator in the list
    for i in range(len(input_list)):
        if is_special_character(input_list[i]):
            last_operator_index = i

    # If an operator is found, check for a period in the substring from that
    # index to the end
    if last_operator_index != -1:
        for i in range(last_operator_index, len(input_list)):
            if input_list[i] == ".":
                return True

    return False


def remove_trailing_zeros(number):
    """Function to remove any irrelevant zeros"""
    # Convert the float to a string with a fixed precision
    num_str = f"{number:.15f}"

    # Remove trailing zeros
    pos = num_str.rstrip("0")
    if pos and pos[-1] == ".":
        return pos[:-1]
    return pos


def perform_operation(operator_stack, value_stack):
    """Function to operate on provided numbers"""
    op = operator_stack.pop()
    operand2 = value_stack.pop()
    operand1 = value_stack.pop()
    result = 0.0

    if op[0] == "*":
        if len(op) > 1 and op[1] == "-":
            result = operand1 * (operand2 * -1)
        else:
            result = operand1 * operand2
    elif op[0] == "+":
        result = operand1 + operand2
    elif op[0] == "-":
        result = operand1 - operand2
    elif op[0] == "/":
        if operand2 != 0:
            result = operand1 / operand2
        else:
            result = float("inf")

    value_stack.append(result)
    return operator_stack, value_stack


def calculate_input(expression):
    """Function to receive expression and prepare it for evaluation"""
    tokens = expression.split()
    operator_stack = []
    value_stack = []

    for token in tokens:
        if token == "(":
            operator_stack.append(token)
        elif token == ")":
            while operator_stack and operator_stack[-1] != "(":
                operator_stack, value_stack = perform_operation(
                    operator_stack, value_stack
                )
            operator_stack.pop()
        elif is_operator(token):
            if token == "-" and (
                not value_stack
                or is_operator(tokens[tokens.index(token) -1 ])
                or tokens[tokens.index(token) - 1] == "("
            ):
                value_stack.append(-1.0)
                operator_stack.append("*")
            else:
                while operator_stack and precedence.get(
                    operator_stack[-1], 0
                ) >= precedence.get(token, 0):
                    operator_stack, value_stack = perform_operation(
                        operator_stack, value_stack
                    )
                operator_stack.append(token)
        else:
            value = parse_number(token)
            value_stack.append(value)

    while operator_stack:
        operator_stack, value_stack = perform_operation(operator_stack, value_stack)

    if len(value_stack) == 1:
        return value_stack[0], ""
    return 0.0, "Invalid expression"


Input = []  # The list that will hold the mathematical expression


class HomePageView(TemplateView):
    """
    Using a generic class based view and specifically TemplateView to
    handle displaying of dynamic data in the template
    """
    template_name  = "index.html"

    def get(self, request, *args, **kwargs):  # Using 'get' method
        global Input
        input_str = get_input_as_string(Input)

        # Go to  the template and pass along the dynamic data that will be
        # displayed in the template
        return self.render_to_response({"input": input_str})


@csrf_exempt
def receive_form(request):
    """
    Using a function-based view to receive input from the template's form and
    operate on it
    """
    if request.method == "POST":
        try:
            global Input
            request.session["isOperator"] = False
            pattern = r"([*\-+/\(\)])"  # Define the regular expression pattern
            operator_pattern = re.compile(pattern)
            operator_position = -1
            last_element_operator = None
            for index, item in enumerate(Input):
                if re.search(operator_pattern, item):
                    operator_position = index
                    break
            for key, value in request.POST.items():
                if (
                    key in ("divide", "multiply", "minus", "add")
                    and request.session["resultDisplayed"] is True
                ):
                    try:
                        del request.session["isOperator"]
                    except KeyError:
                        pass
                    try:
                        del request.session["resultDisplayed"]
                    except KeyError:
                        pass
                    request.session["isOperator"] = True
                    request.session["resultDisplayed"] = False
                if key == "modulus":
                    index_to_slice = operator_position + 1
                    # If the input vector is empty redirect to the html page
                    # and show an empty input box
                    if len(Input) == 0:
                        Input.clear()
                        return redirect("/")
                    sliced_input = Input[index_to_slice:]
                    implode_to_percentage = "".join(sliced_input)
                    to_percentage = None
                    try:
                        to_percentage = float(implode_to_percentage)
                    except ValueError as e:
                        print("Invalid argument: ", e)
                        Input.clear()
                        Input.append("Error")
                    except OverflowError as e:
                        print("Out of range:", e)
                        Input.clear()
                        Input.append("Error")
                    to_percentage /= 100
                    operand_without_modulus = []
                    if index_to_slice > 0:
                        operand_without_modulus = Input[:index_to_slice]

                    # Pattern for a plus or minus
                    first_pattern = r"([*\-+*/()])"
                    first_operator_pattern = re.compile(first_pattern)

                    # Pattern for division or multiplication
                    second_pattern = r"([*/()])"
                    second_operator_pattern = re.compile(second_pattern)
                    plus_in_input = False
                    division_in_input = False
                    negative_in_input = False
                    single_negative_operand = False
                    special_characters = ["+", "-", "*", "/"]
                    if len(Input) > 0:
                        if Input[0] == "-":
                            if not any(
                                item in special_characters for item in Input[1:]

                            ):
                                single_negative_operand = True

                    for element in enumerate(Input):
                        if (
                            request.session.get("multiAndMinus") is True
                            and single_negative_operand is False
                        ):
                            negative_in_input = True
                        elif (
                            re.search(second_operator_pattern, element[1])
                            and single_negative_operand is False
                        ):
                            division_in_input = True
                        elif (
                            re.search(first_operator_pattern, element[1])
                            and single_negative_operand is False
                        ):
                            plus_in_input = True

                    if plus_in_input:
                        operand_without_operator = Input[:operator_position]
                        imploded_operand_str = "".join(operand_without_operator)
                        imploded_operand = -999
                        try:
                            imploded_operand = float(imploded_operand_str)
                        except ValueError as e:
                            print("Invalid argument:", e)
                            Input.clear()
                            Input.append("Error")
                        except OverflowError as e:
                            print("Out of range:", e)
                            Input.clear()
                            Input.append("Error")
                        operand_with_modulus = imploded_operand * to_percentage
                        operand_without_modulus.append(operand_with_modulus)
                        operand_without_modulus_str = "".join(
                            map(str, operand_without_modulus)
                        )
                        current_value_spc = add_whitespace_around_operators(
                            operand_without_modulus_str
                        )
                        current_value_pair = calculate_input(current_value_spc)
                        current_value = None

                        # Check if the second value in the tuple is empty
                        if not current_value_pair[1]:
                            current_value = current_value_pair[0]
                            print(f"Result: {current_value_pair[0]}")
                        else:
                            print(current_value_pair[1])

                        Input.clear()
                        Input.append(remove_trailing_zeros(current_value))
                        try:
                            del request.session["resultDisplayed"]
                        except KeyError:
                            pass
                        request.session["resultDisplayed"] = True
                    elif division_in_input:
                        operand_without_modulus.append(str(to_percentage))
                        operand_without_modulus_str = "".join(operand_without_modulus)
                        current_value_spc = add_whitespace_around_operators(
                            operand_without_modulus_str
                        )
                        current_value_pair = calculate_input(current_value_spc)
                        current_value = None

                        if not current_value_pair[1]:
                            current_value = current_value_pair[0]
                            print(f"Result: {current_value_pair[0]}")
                        else:
                            print(current_value_pair[1])

                        Input.clear()
                        Input.append(remove_trailing_zeros(current_value))
                        try:
                            del request.session["resultDisplayed"]
                        except KeyError:
                            pass
                        request.session["resultDisplayed"] = True

                    elif negative_in_input:
                        operand_without_modulus.append(str(to_percentage))
                        operand_without_modulus_str = "".join(operand_without_modulus)
                        current_value_spc = add_whitespace_around_operators(
                            operand_without_modulus_str
                        )
                        current_value_pair = calculate_input(current_value_spc)
                        current_value = None

                        if not current_value_pair[1]:
                            current_value = current_value_pair[0]
                            print(f"Result: {current_value_pair[0]}")
                        else:
                            print(current_value_pair[1])

                        Input.clear()
                        Input.append(remove_trailing_zeros(current_value))
                        try:
                            del request.session["resultDisplayed"]
                        except KeyError:
                            pass
                        try:
                            del request.session["multiAndMinus"]
                        except KeyError:
                            pass
                        request.session["resultDisplayed"] = True
                        request.session["multiAndMinus"] = False
                    else:
                        current_value_flt = float(get_input_as_string(Input))
                        current_value_flt /= 100
                        Input.clear()
                        Input.append(str(current_value_flt))
                        try:
                            del request.session["resultDisplayed"]
                        except KeyError:
                            pass
                        request.session["resultDisplayed"] = True

                elif key == "equals":
                    if len(Input) == 0:
                        return redirect("/")
                    if is_special_character(Input[-1]):
                        Input.clear()
                        Input.append("Error")
                        return redirect("/")
                    if Input[-1] == "Invalid Expression" or Input[-1] == "Error":
                        Input = Input
                        return redirect("/")

                    input_conv = "".join(Input)
                    current_value_spc = add_whitespace_around_operators(input_conv)
                    current_value_pair = calculate_input(current_value_spc)
                    current_value = None

                    if not current_value_pair[1]:
                        current_value = current_value_pair[0]
                        print(f"Result: {current_value_pair[0]}")
                    else:
                        print(current_value_pair[1])
                        Input.clear()
                        Input.append(current_value_pair[1])
                        try:
                            del request.session["isOperator"]
                        except KeyError:
                            pass
                        try:
                            del request.session["resultDisplayed"]
                        except KeyError:
                            pass
                        request.session["isOperator"] = False
                        request.session["resultDisplayed"] = True
                        return redirect("/")
                    current_value_str = str(current_value)
                    if current_value_str and current_value_str[0] == ".":
                        current_value_str = "0" + current_value_str
                        current_value = float(current_value_str)
                    Input.clear()
                    Input.append(remove_trailing_zeros(current_value))
                    try:
                        del request.session["isOperator"]
                    except KeyError:
                        pass
                    try:
                        del request.session["resultDisplayed"]
                    except KeyError:
                        pass
                    request.session["isOperator"] = False
                    request.session["resultDisplayed"] = True

                elif key == "c":
                    Input.clear()
                    if last_element_operator:
                        last_element_operator = False
                    try:
                        del request.session["isOperator"]
                    except KeyError:
                        pass
                    try:
                        del request.session["resultDisplayed"]
                    except KeyError:
                        pass
                    try:
                        del request.session["multiAndMinus"]
                    except KeyError:
                        pass
                    request.session["isOperator"] = False
                    request.session["resultDisplayed"] = False

                elif key == "delete":
                    if len(Input) > 0:
                        if last_element_operator:
                            last_element_operator = False
                        if (
                            last_element_operator
                            and request.session["multiAndMinus"] is True
                        ):
                            try:
                                del request.session["multiAndMinus"]
                            except KeyError:
                                pass
                        Input.pop()
                    try:
                        del request.session["isOperator"]
                    except KeyError:
                        pass
                    try:
                        del request.session["resultDisplayed"]
                    except KeyError:
                        pass
                    request.session["isOperator"] = False
                    request.session["resultDisplayed"] = False
                else:
                    last_element = None
                    second_last_element = -1
                    if len(Input) > 0:
                        last_element = Input[-1]
                        if is_special_character(last_element):
                            last_element_operator = True
                    if len(Input) > 2:
                        second_last_element = len(Input) - 2
                    second_last_multiply = None
                    if second_last_element != -1 and Input[second_last_element] == "*":
                        second_last_multiply = True
                    if key == "period" and (len(Input) < 1 or last_element_operator):
                        Input.append("0")
                    if last_element == "Invalid expression" or last_element == "Error":
                        Input.clear()
                    if (
                        last_element == "-"
                        and len(Input) == 1
                        and (key == "divide" or key == "multiply" or key == "add")
                    ):
                        Input.clear()

                    if (key == "divide" or key == "multiply" or key == "add") and len(
                        Input
                    ) < 1:
                        Input.clear()
                    elif last_element == "*" and value == "-":
                        request.session["multiAndMinus"] = True
                        Input.append(value)
                    elif (
                        second_last_multiply
                        and last_element == "-"
                        and (key == "divide" or key == "multiply" or key == "add")
                    ):
                        if len(Input) >= 2:
                            Input = Input[:-2]
                            Input.append(value)
                    elif (
                        key == "divide"
                        or key == "multiply"
                        or key == "add"
                        or key == "minus"
                    ) and last_element_operator:
                        if len(Input) > 0:
                            Input = Input[: len(Input) - 1]
                            Input.append(value)
                    elif request.session.get("resultDisplayed") is True:
                        Input.clear()
                        Input.append(value)
                        try:
                            del request.session["resultDisplayed"]
                        except KeyError:
                            pass
                        request.session["resultDisplayed"] = False
                    elif (
                        (period_in_input_func(Input) and found_operator_func(Input) is False)
                        or period_in_last_operand(Input)
                    ) and key == "period":
                        Input = Input
                    else:
                        Input.append(value)
            return redirect("/")
        except Exception as e:
            print(f"Error occurred: {e}")
            Input.clear()
            Input.append("Error")
            return redirect("/")
