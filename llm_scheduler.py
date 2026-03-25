import itertools
import threading
from collections import defaultdict
from langchain_groq import ChatGroq

API_KEYS = [
        "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",
        "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",
    "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",
    "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"
]

class LLMScheduler:
    """
    Round-robin Groq scheduler with:
    - Multiple accounts
    - Thread safety
    - Automatic failover
    - Token usage logging
    """

    def __init__(
        self,
        api_keys,
        model="qwen/qwen3-32b",
        temperature=0,
        reasoning_format="parsed",
        max_retries=2,
    ):
        self.lock = threading.Lock()

        self.llms = []
        self.account_labels = []

        for i, key in enumerate(api_keys):
            llm = ChatGroq(
                model=model,
                temperature=temperature,
                reasoning_format=reasoning_format,
                max_retries=max_retries,
                api_key=key,
            )
            self.llms.append(llm)
            self.account_labels.append(f"account_{i+1}")

        self.cycle = itertools.cycle(range(len(self.llms)))

        self.token_usage = defaultdict(int)
        self.call_count = defaultdict(int)

    def invoke(self, messages):
        for _ in range(len(self.llms)):

            with self.lock:
                idx = next(self.cycle)

            llm = self.llms[idx]
            account = self.account_labels[idx]

            try:
                response = llm.invoke(messages)

                usage = getattr(response, "usage_metadata", {}) or {}
                total = usage.get("total_tokens", 0)

                self.token_usage[account] += total
                self.call_count[account] += 1

                print(
                    f"[{account}] Call #{self.call_count[account]} | "
                    f"Total Tokens: {total}"
                )

                return response

            except Exception as e:
                print(f"[{account}] FAILED → {e}")
                continue

        raise Exception("All Groq accounts failed.")

    def print_usage_report(self):
        print("\n========== TOKEN USAGE REPORT ==========")
        for account in self.account_labels:
            print(
                f"{account} | Calls: {self.call_count[account]} | "
                f"Tokens: {self.token_usage[account]}"
            )
        print("========================================\n")
