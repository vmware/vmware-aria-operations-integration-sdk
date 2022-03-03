from PyInquirer import style_from_dict, Token

vrops_sdk_prompt_style = style_from_dict({
    Token.QuestionMark: "#E91E63 bold",
    Token.Selected: "#673AB7 bold",
    Token.Instruction: "",  # default
    Token.Answer: "#2196f3 bold",
    Token.Question: "",
})
