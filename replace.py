import os
import time
import datetime
import argparse
import concurrent.futures
import re
from gepetto import gpt, ollama, groq, mistral, claude
from prompts import system_prompts
from yaspin import yaspin

def get_bot(model="gpt-4o"):
    if model.startswith('gpt'):
        bot = gpt.GPTModelSync()
    elif model.startswith('claude'):
        bot = claude.ClaudeModelSync()
    return bot

def talk_to_llm(messages, model="gpt-4o"):
    # sleep for 20 seconds to avoid rate limiting
    # time.sleep(20)
    bot = get_bot(model)
    print(f"Talking to {model}... using bot {bot.name}")
    response = bot.chat(messages, model=model)
    response.message = re.sub(r'```(html|markdown|blade)', '', response.message)
    response.message = re.sub(r'```', '', response.message).strip()
    return response

def convert_template(filename, a11y=False, responsive=False, css=False, model="gpt-4o", component=True):
    print(f"Converting {filename}...")
    with open(filename, "r") as file:
        updated_template = file.read()
        total_cost = 0
        if css:
            messages = [
                {"role": "system", "content": system_prompts["template_to_components"]},
                {"role": "user", "content": f"Could you convert this BulmaCSS laravel blade template to use my blade components and update any extra css to modern TailwindCSS?\n\n```{updated_template}```"},
            ]
            response = talk_to_llm(messages, model=model)
            updated_template = response.message
            total_cost += response.cost
        # ensure all directories in the full fulename exist before writing it
        os.makedirs(os.path.dirname(f"ff/{filename}"), exist_ok=True)
        with open(f"ff/{filename}", "w") as file:
            file.write(updated_template)
        return f"ff/{filename}", total_cost

def process_file(filename, a11y=False, responsive=False, css=False, model="gpt-3.5-turbo"):
    _, cost = convert_template(filename, a11y, responsive, css, model)
    return cost

def main(file="", dir="", a11y=False, responsive=False, css=False, model="gpt-4o"):
    if not os.path.exists("ff"):
        os.makedirs("ff")
    total_cost = 0
    start_time = datetime.datetime.now()
    file_list = []
    if not dir:
        dir = '.'
    if file:
        file_list.append(file)
    else:
        for root, dirs, files in os.walk(dir):
            for filename in files:
                if filename.endswith(".blade.php"):
                    full_path = os.path.join(root, filename)
                    if full_path.startswith("./"):
                        full_path = full_path[2:]
                    file_list.append(full_path)

    costs = []
    for filename in file_list:
        cost = process_file(filename, a11y, responsive, css, model)
        costs.append(cost)
    # with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    #     costs = executor.map(process_file, file_list, [a11y]*len(file_list), [responsive]*len(file_list), [css]*len(file_list), [model]*len(file_list))

    total_cost = sum(costs)
    end_time = datetime.datetime.now()
    elapsed_time = (end_time - start_time).total_seconds()
    print(f"\n\nTotal time: {round(elapsed_time, 2)} seconds")
    print(f"Total cost: {round(total_cost, 5)}")

if __name__ == "__main__":
    argp = argparse.ArgumentParser()
    argp.add_argument("--file", type=str, default="", help="A single file to convert")
    argp.add_argument("--dir", type=str, default="", help="The directory to convert")
    argp.add_argument("--model", type=str, default="gpt-4o", help="The LLM model to use")
    argp.add_argument("--css", action="store_true", default=False, help="Convert CSS from Bulma to Tailwind")
    argp.add_argument("--a11y", action="store_true", default=False, help="Do accessibilty checks and code")
    argp.add_argument("--responsive", action="store_true", default=False, help="Do responsive checks and code")
    args = argp.parse_args()

    main(file=args.file, dir=args.dir, a11y=args.a11y, responsive=args.responsive, css=args.css, model=args.model)
