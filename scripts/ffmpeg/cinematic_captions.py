def escape_drawtext_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
    )


def escape_drawtext_expression(expression: str) -> str:
    return expression.replace(",", "\\,")


def caption_alpha_expression(
    start: float,
    end: float,
    fade: float,
    fade_out: bool = True,
) -> str:
    fade_in = min(fade, max(0.0, end - start))
    if fade_out:
        fade_out_start = max(start + fade_in, end - fade)
        expression = (
            f"if(lt(t,{start:.3f}),0,"
            f"if(lt(t,{start + fade_in:.3f}),"
            f"(t-{start:.3f})/{fade_in:.3f},"
            f"if(lt(t,{fade_out_start:.3f}),0.92,"
            f"if(lt(t,{end:.3f}),"
            f"0.92*(1-(t-{fade_out_start:.3f})/"
            f"{end - fade_out_start:.3f}),0))))"
        )
    else:
        expression = (
            f"if(lt(t,{start:.3f}),0,"
            f"if(lt(t,{start + fade_in:.3f}),"
            f"(t-{start:.3f})/{fade_in:.3f},0.92))"
        )
    return escape_drawtext_expression(expression)


def build_cinematic_caption_filter(
    captions: list[dict],
    *,
    input_label: str,
    output_label: str,
    font_family: str,
    text_color: str,
    shadow_color: str,
    fade: float,
) -> str:
    if not captions:
        return f"[{input_label}]null[{output_label}]"

    filters = []
    current_label = input_label

    for index, caption in enumerate(captions):
        next_label = (
            output_label
            if index == len(captions) - 1
            else f"caption_stage_{index}"
        )
        text = escape_drawtext_text(
            caption.get("display_text", caption["text"])
        )
        alpha = caption_alpha_expression(
            caption["start"],
            caption["end"],
            fade,
            caption.get("fade_out", True),
        )
        enable = escape_drawtext_expression(
            f"between(t,{caption['start']:.3f},{caption['end']:.3f})"
        )
        border_width = caption.get("border_width", 1)
        border_opacity = caption.get("border_opacity", 0.22)
        shadow_opacity = caption.get("shadow_opacity", 0.42)
        filters.append(
            f"[{current_label}]"
            f"drawtext="
            f"font='{font_family}':"
            f"text='{text}':"
            f"fontsize={caption['font_size']}:"
            f"fontcolor={text_color}:"
            f"alpha='{alpha}':"
            f"x={caption['x']}:"
            f"y={caption['y']}:"
            f"bordercolor={shadow_color}@{border_opacity}:"
            f"borderw={border_width}:"
            f"shadowcolor={shadow_color}@{shadow_opacity}:"
            f"shadowx=0:"
            f"shadowy=3:"
            f"enable='{enable}'"
            f"[{next_label}]"
        )
        current_label = next_label

    return ";".join(filters)
