phrases = []
def long_string(index, l):
    """Function to identify multiple words as phrase in the input string"""
    global phrases
    stack = []
    w = []
    for k, p in enumerate(l):
        if p == '"':
            if len(stack) == 0:
                stack.append(p)
            else:
                stack.pop()
                phrases.append(" ".join(w))
                return " ".join(w), k
        else:
            w.append(p)
    phrases.append(" ".join(w))
    return " ".join(w), k
            

def find_section(index, l):
    """Function to identify sections if any in the input string"""
    stack = []
    c = 0
    w = []
    for k, p in enumerate(l):
        if p == "(":
            if len(stack) == 0:
                stack.append("(")
            else:
                x, y = find_section(k, l[k:])
                w.append(x)
                c += y
        elif k < c:
            continue
        elif p == ")":
            if stack[-1] == "(":
                stack.pop()
                if len(stack) == 0:
                    return w, k
        elif p == '"':
            long_word, y = long_string(k, l[k:])
            w.append(long_word)
            c += y
        else:
            w.append(p)
        c += 1
    return w, k

def parse_string(s):
    """Function to convert input string into user manageable List"""
    s = s.replace("(", " ( ").replace(")", " ) ").replace('"', ' " ')
    split_words = s.split()
    i = 0
    conditions = []
    while i < len(split_words):
        j = split_words[i]
        if "(" in j:
            sec, c = find_section(i, split_words[i:])
            i = c+i
            conditions.append(sec)
        elif "\"" in j:
            w, c = long_string(i, split_words[i:])
            w = "\"{}\"".format(w)
            conditions.append(w)
            i += c
        elif j == "AND" or j == "OR":
            conditions.append(j)
        else:
            if j != ")" or j != '\"':
                conditions.append(j)
        i += 1
    return conditions


def parsed_string_to_elasticsearch_query(parsed_string):
    """Function to convert parsed string to elasticsearch query"""
    items = ""
    for item in parsed_string:
        if type(item) is list:
            items += " (" + parsed_string_to_elasticsearch_query(item) + ")"
        else:
            if " " in item.strip():
                items += "\"" + str(item) + "\""
            else:
                items += " " + item
                items = items.strip()
    return items

def parsed_string_to_mysql_query(parsed_string):
    qs = ""
    l = []
    for i, item in enumerate(parsed_string):
        if type(item) is list:
            parsed_string[i] = parsed_string_to_mysql_query(item)
    else:
        item = parsed_string
        if len(item) == 3:
            a = item[0]
            b = item[2]
            if a in phrases:
                a = "\"" + a +"\""
            if b in phrases:
                b = "\"" + b + "\""
            
            if item[1] == "AND":
                qs = "(+{} +{})".format(a, b)
            else:
                qs = "({} {})".format(a, b)
        elif len(item) > 3:
            reformat = []
            for i, k in enumerate(item):
                if k == "AND":
                    a = item[i-1]
                    b = item[i+1]
                    if a in phrases:
                        a = "\"" + a +"\""
                    if b in phrases:
                        b = "\"" + b + "\""
                    qs = "(+{} +{})".format(a, b)
                    reformat.pop()
                    reformat.append(qs)
                    if i+1 < len(item):
                        reformat += item[i+1:]
                    break
                else:
                    if i == len(item)-1:
                        a = item[i-2]
                        b = k
                        if a in phrases:
                            a = "\"" + a +"\""
                        if b in phrases:
                            b = "\"" + b + "\""
                        qs = "({} {})".format(a, b)
                        reformat = reformat[0:i-2]
                        reformat.append(qs)
                    else:
                        reformat.append(k)
            return parsed_string_to_mysql_query(reformat)
        else:
            return parsed_string
    return qs

def parser(input_string, output_format):
    """Function which takes string as input and coverts it as query into selected format"""
    global phrases
    parsed_string = parse_string(input_string)
    phrases = list(set(phrases))
    if output_format == "elasticsearch":
        output = parsed_string_to_elasticsearch_query(parsed_string)
        query = {
            "query": {
                "query_string": {
                    "query": output,
                    "default_field": "resume_text"
                }
            }
        }
        return query
    elif output_format == "sql":
        query = parsed_string_to_mysql_query(parsed_string)
        query = "SELECT * FROM candidates WHERE MATCH(resume_text) AGAINST('{}' IN BOOLEAN MODE)".format(query)
        return query

if __name__ == "__main__":
    input_string = input("input string: ")
    output_format = input("output format should be either sql or elasticsearch : ")
    output = parser(input_string, output_format)
    print("*"*20, "OUTPUT", "*"*20, end="\n\n")
    print(output, end= "\n\n")
    print("**"*24)