enum Mood
{
    CALM = 3,
    ANGRY
}

function scr_helper_uses_enum()
{
    return Mood.CALM + Mood.ANGRY;
}
