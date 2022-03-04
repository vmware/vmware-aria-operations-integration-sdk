from PyInquirer import style_from_dict, Token

VERSION_FILE = "container_versions.json"
PY_INQUIRER_STYLE = style_from_dict({
    Token.QuestionMark: "#E91E63 bold",
    Token.Selected: "#673AB7 bold",
    Token.Instruction: "",
    Token.Answer: "#2196f3 bold",
    Token.Question: "",
})