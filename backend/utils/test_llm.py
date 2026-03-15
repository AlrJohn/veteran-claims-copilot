from llm_client import call_llm

if __name__ == "__main__":
    result = call_llm("Say hello in one short sentence.")
    print(result)