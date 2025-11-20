# -*- coding: utf-8 -*-
"""
Diff/Patching Utility
=====================

This module provides tools for applying a custom SEARCH/REPLACE diff format
to a given string content. It is a Python port of a robust TypeScript
implementation, designed to handle multi-level fallbacks for matching search blocks.

Author: Gaoyuan (ported to Python)
"""

import re
from typing import List, Tuple, Dict, Any
from difflib import SequenceMatcher

# Regex patterns for identifying SEARCH/REPLACE block markers
SEARCH_BLOCK_START_REGEX = re.compile(r"^[-]{7,} SEARCH$")
SEARCH_BLOCK_END_REGEX = re.compile(r"^[=]{7,}$")
REPLACE_BLOCK_END_REGEX = re.compile(r"^[+]{7,} REPLACE$")

def is_search_block_start(line: str) -> bool:
    """Checks if a line is a SEARCH block start marker."""
    return bool(SEARCH_BLOCK_START_REGEX.match(line))

def is_search_block_end(line: str) -> bool:
    """Checks if a line is a SEARCH block end marker."""
    return bool(SEARCH_BLOCK_END_REGEX.match(line))

def is_replace_block_end(line: str) -> bool:
    """Checks if a line is a REPLACE block end marker."""
    return bool(REPLACE_BLOCK_END_REGEX.match(line))

def fuzzy_match(original_content: str, search_content: str) -> Tuple[int, int] or None:
    """
    Attempts a fuzzy match using difflib.SequenceMatcher. This is a more robust
    fallback that can handle minor content variations.
    """
    original_lines = original_content.splitlines(True) # Keep endings for accurate indexing
    search_lines = search_content.splitlines(True)

    if not search_lines:
        return None

    # SequenceMatcher works on sequences. Here, our sequences are lists of lines.
    s = SequenceMatcher(None, original_lines, search_lines, autojunk=False)
    
    # find_longest_match gives us the longest contiguous matching subsequence.
    # It returns a Match(a, b, n) tuple where original_lines[a:a+n] == search_lines[b:b+n].
    match = s.find_longest_match(0, len(original_lines), 0, len(search_lines))

    # We need to decide if this match is "good enough".
    # A simple heuristic: the match should cover a significant portion of the search block.
    # For instance, at least 60% of the lines in the search block must match.
    # We also need to ensure the match is not trivial (e.g., just one matching line).
    if match.size > 0 and (match.size / len(search_lines)) >= 0.6:
        
        # We assume the user wants to replace the code block that *contains* the best match,
        # and has the same size as the search block. We "anchor" the replacement on this best match.
        # The start of the replacement block in the original text is derived from where the
        # best match starts.
        
        start_line_in_original = match.a - match.b
        end_line_in_original = start_line_in_original + len(search_lines)

        if start_line_in_original < 0 or end_line_in_original > len(original_lines):
            # The derived block would be out of bounds.
            return None

        # Calculate character indices
        match_start_char_index = sum(len(line) for line in original_lines[:start_line_in_original])
        
        # The content to be replaced is the slice of original_lines
        content_to_replace = original_lines[start_line_in_original:end_line_in_original]
        match_end_char_index = match_start_char_index + sum(len(line) for line in content_to_replace)

        return match_start_char_index, match_end_char_index

    return None

def line_trimmed_fallback_match(original_content: str, search_content: str, start_index: int) -> Tuple[int, int] or None:
    """
    Attempts a line-trimmed fallback match.

    It tries to match `search_content` lines against a block of lines in `original_content`
    starting from `start_index`. Lines are matched by trimming leading/trailing whitespace.

    Returns (match_start_index, match_end_index) if found, or None.
    """
    original_lines = original_content.splitlines()
    search_lines = search_content.splitlines()

    if not search_lines:
        return None

    # Find the line number where start_index falls
    start_line_num = original_content.count('\n', 0, start_index)

    for i in range(start_line_num, len(original_lines) - len(search_lines) + 1):
        matches = True
        for j in range(len(search_lines)):
            if original_lines[i + j].strip() != search_lines[j].strip():
                matches = False
                break
        
        if matches:
            # Calculate exact character positions
            match_start_char_index = 0
            for k in range(i):
                match_start_char_index += len(original_lines[k]) + 1  # +1 for \n

            match_end_char_index = match_start_char_index
            for k in range(len(search_lines)):
                match_end_char_index += len(original_lines[i + k]) + 1
            
            # The last newline is not part of the content
            match_end_char_index -=1 

            return match_start_char_index, match_end_char_index

    return None

def block_anchor_fallback_match(original_content: str, search_content: str, start_index: int) -> Tuple[int, int] or None:
    """
    Attempts to match blocks of code by using the first and last lines as anchors.
    This is a third-tier fallback strategy for blocks of 3 or more lines.
    """
    original_lines = original_content.splitlines()
    search_lines = search_content.splitlines()

    if len(search_lines) < 3:
        return None

    first_line_search = search_lines[0].strip()
    last_line_search = search_lines[-1].strip()
    search_block_size = len(search_lines)

    start_line_num = original_content.count('\n', 0, start_index)

    for i in range(start_line_num, len(original_lines) - search_block_size + 1):
        if original_lines[i].strip() != first_line_search:
            continue
        if original_lines[i + search_block_size - 1].strip() != last_line_search:
            continue

        # Found a match, calculate character positions
        match_start_char_index = 0
        for k in range(i):
            match_start_char_index += len(original_lines[k]) + 1

        match_end_char_index = match_start_char_index
        for k in range(search_block_size):
            match_end_char_index += len(original_lines[i + k]) + 1
        
        match_end_char_index -= 1 # The last newline is not part of the content

        return match_start_char_index, match_end_char_index

    return None


def apply_diff(original_content: str, diff_content: str) -> str:
    """
    Applies a streamed diff in a specialized SEARCH/REPLACE block format to the
    original file content.

    Args:
        original_content: The original content of the file.
        diff_content: The diff content with one or more SEARCH/REPLACE blocks.

    Returns:
        The reconstructed file content.

    Raises:
        ValueError: If a SEARCH block cannot be matched.
    """
    lines = diff_content.splitlines()
    
    replacements: List[Dict[str, Any]] = []
    
    in_search = False
    in_replace = False
    current_search_content_lines = []
    current_replace_content_lines = []

    for line in lines:
        if is_search_block_start(line):
            if in_search or in_replace:
                raise ValueError("Unexpected SEARCH_BLOCK_START found.")
            in_search = True
            current_search_content_lines = []
            current_replace_content_lines = []
            continue

        if is_search_block_end(line):
            if not in_search:
                raise ValueError("Unexpected SEARCH_BLOCK_END without a start.")
            in_search = False
            in_replace = True
            continue

        if is_replace_block_end(line):
            if not in_replace:
                raise ValueError("Unexpected REPLACE_BLOCK_END without a start.")
            
            search_content = "\n".join(current_search_content_lines)
            
            # =================================================================
            # 四层回退匹配策略：提高AI生成的SEARCH块的匹配成功率
            # =================================================================
            # 由于大语言模型生成的SEARCH块可能不完全精确（如存在微小的空格差异、
            # 缩进变化、或部分内容遗漏），我们采用逐级回退的匹配策略来提高
            # 匹配的健壮性，从最严格的精确匹配逐步降低到最宽松的锚点匹配。
            
            search_match_index = -1
            search_end_index = -1

            # 策略1: 精确匹配 (Exact Match)
            # 尝试在原文中找到与SEARCH块完全相同的文本。这是最可靠的方法，
            # 但要求AI生成的SEARCH块与原文完全一致，包括空格和换行符。
            exact_index = original_content.find(search_content)
            if exact_index != -1:
                search_match_index = exact_index
                search_end_index = exact_index + len(search_content)
            else:
                # 策略2: 模糊匹配 (Fuzzy Match using difflib)
                # 使用Python difflib库的序列匹配算法，可以容忍一定程度的文本差异。
                # 当AI生成的SEARCH块与原文有微小差异时（如多/少几个字符、轻微的格式变化），
                # 此策略可以找到最佳的近似匹配。要求至少60%的内容匹配。
                fuzzy_match_result = fuzzy_match(original_content, search_content)
                if fuzzy_match_result:
                    search_match_index, search_end_index = fuzzy_match_result
                else:
                    # 策略3: 忽略空格的行匹配 (Line-trimmed Fallback)
                    # 逐行比较时忽略每行首尾的空白字符。这对于处理缩进不一致
                    # 或AI生成时添加/删除了额外空格的情况特别有效。
                    line_match = line_trimmed_fallback_match(original_content, search_content, 0)
                    if line_match:
                        search_match_index, search_end_index = line_match
                    else:
                        # 策略4: 代码块锚点匹配 (Block Anchor Fallback)
                        # 当SEARCH块有3行以上时，仅使用第一行和最后一行作为"锚点"
                        # 来定位代码块。这是最宽松的策略，适用于AI生成的SEARCH块
                        # 中间部分有较大差异，但首尾行相对准确的情况。
                        block_match = block_anchor_fallback_match(original_content, search_content, 0)
                        if block_match:
                            search_match_index, search_end_index = block_match
                        else:
                            # 所有策略都失败：抛出详细的错误信息
                            raise ValueError(f"The SEARCH block does not match anything in the file:\n---\n{search_content}\n---")
            
            replacements.append({
                "start": search_match_index,
                "end": search_end_index,
                "content": "\n".join(current_replace_content_lines),
            })

            # Reset for next block
            in_replace = False
            in_search = False
            current_search_content_lines = []
            current_replace_content_lines = []
            continue

        if in_search:
            current_search_content_lines.append(line)
        elif in_replace:
            current_replace_content_lines.append(line)
    
    if in_search or in_replace:
        raise ValueError("Diff content ended while inside a SEARCH/REPLACE block. Missing closing marker.")

    # Sort replacements by start position to handle them in order
    replacements.sort(key=lambda r: r['start'])
    
    # Check for overlapping replacements
    last_end = -1
    for r in replacements:
        if r['start'] < last_end:
            raise ValueError("Overlapping SEARCH blocks are not supported.")
        last_end = r['end']

    # Rebuild the entire result by applying all replacements
    result = []
    current_pos = 0
    for replacement in replacements:
        result.append(original_content[current_pos:replacement['start']])
        result.append(replacement['content'])
        current_pos = replacement['end']
    
    result.append(original_content[current_pos:])
    
    return "".join(result) 