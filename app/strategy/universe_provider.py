from config import (
    CODE_CONDITION_MAX_UNIVERSE_SIZE,
    CODE_CONDITION_UNIVERSE_CODES,
    CODE_CONDITION_UNIVERSE_TYPE,
)


class UniverseProvider:
    def get_codes(self):
        if CODE_CONDITION_UNIVERSE_TYPE != "manual":
            raise ValueError(
                f"지원하지 않는 universe type입니다: {CODE_CONDITION_UNIVERSE_TYPE}"
            )

        codes = []

        for code in CODE_CONDITION_UNIVERSE_CODES:
            code_text = str(code).strip()

            if not code_text:
                continue

            codes.append(code_text)

            if len(codes) >= CODE_CONDITION_MAX_UNIVERSE_SIZE:
                break

        return codes