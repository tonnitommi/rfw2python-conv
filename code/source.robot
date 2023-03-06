*** Settings ***
Library     RPA.Robocorp.Vault
Library     RPA.Notifier


*** Tasks ***
One task only
    Do the thing    This is my important message.


*** Keywords ***
Do the thing
    [Arguments]    ${message}

    ${slack_secret}=    Get Secret    Slack

    Notify Slack
    ...    message=${message}
    ...    channel=${slack_secret}[channel]
    ...    webhook_url=${slack_secret}[webhook]
