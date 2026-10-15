from rich.align import Align
from rich.panel import Panel
from rich.text import Text

from src.config import settings


def print_banner():
    banner = """
 .S_SSSs     .S_SSSs     .S_SSSs     .S_sSSs           .S    S.    .S_SSSs           .S_SSSs     .S         .S_SSSs      sSSs_sSSs    sdSS_SSSSSSbs  
.SS~SSSSS   .SS~SSSSS   .SS~SSSSS   .SS~YS%%b         .SS    SS.  .SS~SSSSS         .SS~SSSSS   .SS        .SS~SSSSS    d%%SP~YS%%b   YSSS~S%SSSSSP  
S%S   SSSS  S%S   SSSS  S%S   SSSS  S%S   `S%b        S%S    S&S  S%S   SSSS        S%S   SSSS  S%S        S%S   SSSS  d%S'     `S%b       S%S       
S%S    S%S  S%S    S%S  S%S    S%S  S%S    S%S        S%S    d*S  S%S    S%S        S%S    S%S  S%S        S%S    S%S  S%S       S%S       S%S       
S%S SSSS%P  S%S SSSS%S  S%S SSSS%S  S%S    d*S        S&S   .S*S  S%S SSSS%S        S%S SSSS%S  S&S        S%S SSSS%P  S&S       S&S       S&S       
S&S  SSSY   S&S  SSS%S  S&S  SSS%S  S&S   .S*S        S&S_sdSSS   S&S  SSS%S        S&S  SSS%S  S&S        S&S  SSSY   S&S       S&S       S&S       
S&S    S&S  S&S    S&S  S&S    S&S  S&S_sdSSS         S&S~YSSY%b  S&S    S&S        S&S    S&S  S&S        S&S    S&S  S&S       S&S       S&S       
S&S    S&S  S&S    S&S  S&S    S&S  S&S~YSSY          S&S    `S%  S&S    S&S        S&S    S&S  S&S        S&S    S&S  S&S       S&S       S&S       
S*S    S&S  S*S    S&S  S*S    S&S  S*S               S*S     S%  S*S    S&S        S*S    S&S  S*S        S*S    S&S  S*b       d*S       S*S       
S*S    S*S  S*S    S*S  S*S    S*S  S*S               S*S     S&  S*S    S*S        S*S    S*S  S*S        S*S    S*S  S*S.     .S*S       S*S       
S*S SSSSP   S*S    S*S  S*S    S*S  S*S               S*S     S&  S*S    S*S        S*S    S*S  S*S        S*S SSSSP    SSSbs_sdSSS        S*S       
S*S  SSY    SSS    S*S  SSS    S*S  S*S               S*S     SS  SSS    S*S        SSS    S*S  S*S        S*S  SSY      YSSP~YSSY         S*S       
SP                 SP          SP   SP                SP                 SP                SP   SP         SP                              SP        
Y                  Y           Y    Y                 Y                  Y                 Y    Y          Y                               Y         

    """
    console = settings.console
    console.print(
        Align.center(
            Panel.fit(
                Text(banner, style="bold magenta"),
                title="LangGraph Chatbot",
                subtitle="made by pirate",
                style="bold blue",
            )
        )
    )
