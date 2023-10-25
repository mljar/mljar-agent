import os
import csv 


def guess_delimiter(fname):
    try:
        with open(fname, newline='') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))   
            if dialect.delimiter == "\t":
                return "\\t"
            return dialect.delimiter
    except Exception as e:
        print(str(e))
        pass
    return ","

def files_to_prompt(wd, files):
        prompt = ""
        for f in files:
            fpath = os.path.join(wd, f)
            content = ""
            with open(fpath, "r") as fin:
                content = fin.read()
            lines = content.split("\n")

            delimiter_str = ""
            if fpath.endswith(".csv"):
                delimiter = guess_delimiter(fpath)
                delimiter_str = f" (delimiter \"{delimiter}\") "
            if len(lines) == 0:
                prompt += f"\n - file {f} is empty\n\n"
            elif len(lines) < 15:
                prompt += f"\n - file {f}{delimiter_str} includes\n\n"
                prompt += "```\n"
                prompt += content + "```\n\n"
            else:
                prompt += f"\n - file {f}{delimiter_str} has {len(lines)} lines, below are first 15 lines from it\n\n```"
                for l in lines[:15]:
                    prompt += f"{l}\n"
                prompt += "```\n\n"
        return prompt

if __name__ == "__main__":
    print(guess_delimiter("/home/piotr/sandbox/mljar-agent/benchmark/agbenchmark/challenges/verticals/data/1_sort_csv/artifacts_in//input.csv"))
    print(guess_delimiter("/home/piotr/sandbox/mljar-agent/benchmark/agbenchmark/challenges/verticals/data/4_answer_question_small_csv/artifacts_in/file1.csv"))
