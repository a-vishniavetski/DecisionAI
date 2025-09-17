EXTRACTOR_PROMPT="Decide if the question is a binary decision question."\
"That is, there are two opposing sides to the question."\
"If so, extract the binary pro and con positions. "\
"A pro position is a positive statement, that agrees, shows supports, or otherise take the positive side in the debate."\
"A con position is a negative statement, that disagrees, shows opposes, or otherwise takes the negative side in the debate."\
"If such dialectical separation is not possible, return empty strings.\nQuestion: {user_msg}\n"\
"Return the result as a JSON object with keys 'pro' and 'con', and only the JSON object."