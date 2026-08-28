/**
 * Arabic Reshaper & BiDi Support for Web Terminal
 * Converts raw Arabic characters into contextual joined glyphs (Initial, Medial, Final, Isolated)
 * and reverses character order within Arabic words so they render correctly in LTR terminal grids.
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.ArabicShaper = factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {

    // Unicode mappings for Arabic Letters [Isolated, Final, Initial, Medial]
    const ARABIC_GLYPHS = {
        0x0621: [0xFE80, 0xFE80, 0xFE80, 0xFE80], // Hamza
        0x0622: [0xFE81, 0xFE82, 0xFE81, 0xFE82], // Alef Madda
        0x0623: [0xFE83, 0xFE84, 0xFE83, 0xFE84], // Alef Hamza Above
        0x0624: [0xFE85, 0xFE86, 0xFE85, 0xFE86], // Waw Hamza Above
        0x0625: [0xFE87, 0xFE88, 0xFE87, 0xFE88], // Alef Hamza Below
        0x0626: [0xFE89, 0xFE8A, 0xFE8B, 0xFE8C], // Yeh Hamza Above
        0x0627: [0xFE8D, 0xFE8E, 0xFE8D, 0xFE8E], // Alef
        0x0628: [0xFE8F, 0xFE90, 0xFE91, 0xFE92], // Beh
        0x0629: [0xFE93, 0xFE94, 0xFE93, 0xFE94], // Teh Marbuta
        0x062A: [0xFE95, 0xFE96, 0xFE97, 0xFE98], // Teh
        0x062B: [0xFE99, 0xFE9A, 0xFE9B, 0xFE9C], // Theh
        0x062C: [0xFE9D, 0xFE9E, 0xFE9F, 0xFEA0], // Jeem
        0x062D: [0xFEA1, 0xFEA2, 0xFEA3, 0xFEA4], // Hah
        0x062E: [0xFEA5, 0xFEA6, 0xFEA7, 0xFEA8], // Khah
        0x062F: [0xFEA9, 0xFEAA, 0xFEA9, 0xFEAA], // Dal
        0x0630: [0xFEAB, 0xFEAC, 0xFEAB, 0xFEAC], // Thal
        0x0631: [0xFEAD, 0xFEAE, 0xFEAD, 0xFEAE], // Reh
        0x0632: [0xFEAF, 0xFEB0, 0xFEAF, 0xFEB0], // Zain
        0x0633: [0xFEB1, 0xFEB2, 0xFEB3, 0xFEB4], // Seen
        0x0634: [0xFEB5, 0xFEB6, 0xFEB7, 0xFEB8], // Sheen
        0x0635: [0xFEB9, 0xFEBA, 0xFEBB, 0xFEBC], // Sad
        0x0636: [0xFEBD, 0xFEBE, 0xFEBF, 0xFEC0], // Dad
        0x0637: [0xFEC1, 0xFEC2, 0xFEC3, 0xFEC4], // Tah
        0x0638: [0xFEC5, 0xFEC6, 0xFEC7, 0xFEC8], // Zah
        0x0639: [0xFEC9, 0xFECA, 0xFECB, 0xFECC], // Ain
        0x063A: [0xFECD, 0xFECE, 0xFECF, 0xFED0], // Ghain
        0x0641: [0xFED1, 0xFED2, 0xFED3, 0xFED4], // Feh
        0x0642: [0xFED5, 0xFED6, 0xFED7, 0xFED8], // Qaf
        0x0643: [0xFED9, 0xFEDA, 0xFEDB, 0xFEDC], // Kaf
        0x0644: [0xFEDD, 0xFEDE, 0xFEDF, 0xFEE0], // Lam
        0x0645: [0xFEE1, 0xFEE2, 0xFEE3, 0xFEE4], // Meem
        0x0646: [0xFEE5, 0xFEE6, 0xFEE7, 0xFEE8], // Noon
        0x0647: [0xFEE9, 0xFEEA, 0xFEEB, 0xFEEC], // Heh
        0x0648: [0xFEED, 0xFEEE, 0xFEED, 0xFEEE], // Waw
        0x0649: [0xFEEF, 0xFEF0, 0xFBE8, 0xFBE9], // Alef Maksura
        0x064A: [0xFEF1, 0xFEF2, 0xFEF3, 0xFEF4], // Yeh
        0x067E: [0xFB56, 0xFB57, 0xFB58, 0xFB59], // Peh
        0x0686: [0xFB7A, 0xFB7B, 0xFB7C, 0xFB7D], // Tcheh
        0x0698: [0xFB8A, 0xFB8B, 0xFB8A, 0xFB8B], // Jeh
        0x06AF: [0xFB92, 0xFB93, 0xFB94, 0xFB95], // Gaf
    };

    // Characters that do NOT connect to the following letter
    const RIGHT_CONNECTING_ONLY = new Set([
        0x0621, 0x0622, 0x0623, 0x0624, 0x0625, 0x0627, 0x0629, 0x062F, 0x0630, 
        0x0631, 0x0632, 0x0648, 0x0649, 0x0698, 0xFE80, 0xFE81, 0xFE82, 0xFE83, 
        0xFE84, 0xFE85, 0xFE86, 0xFE87, 0xFE88, 0xFE8D, 0xFE8E, 0xFE93, 0xFE94, 
        0xFEA9, 0xFEAA, 0xFEAB, 0xFEAC, 0xFEAD, 0xFEAE, 0xFEAF, 0xFEB0, 0xFEED, 0xFEEE
    ]);

    // Tashkeel / Harakat characters
    const TASHKEEL = new Set([
        0x064B, 0x064C, 0x064D, 0x064E, 0x064F, 0x0650, 0x0651, 0x0652, 0x0670
    ]);

    function isArabicChar(code) {
        return (code >= 0x0600 && code <= 0x06FF) || (code >= 0x0750 && code <= 0x077F) || (code >= 0xFB50 && code <= 0xFDFF) || (code >= 0xFE70 && code <= 0xFEFF);
    }

    function canConnectPrev(code) {
        if (!code || TASHKEEL.has(code)) return false;
        return ARABIC_GLYPHS[code] !== undefined;
    }

    function canConnectNext(code) {
        if (!code || TASHKEEL.has(code)) return false;
        if (!ARABIC_GLYPHS[code]) return false;
        return !RIGHT_CONNECTING_ONLY.has(code);
    }

    // Reshapes a single Arabic word / run
    function reshapeWord(word) {
        if (!word) return word;

        // Filter out tashkeel for clean terminal rendering
        const chars = Array.from(word).filter(c => !TASHKEEL.has(c.charCodeAt(0)));
        const len = chars.length;
        const result = [];
        let i = 0;

        while (i < len) {
            const code = chars[i].charCodeAt(0);

            if (!ARABIC_GLYPHS[code]) {
                result.push(chars[i]);
                i++;
                continue;
            }

            // Handle Lam-Alef Ligatures
            if (code === 0x0644 && i + 1 < len) {
                const nextCode = chars[i + 1].charCodeAt(0);
                const prevCode = i > 0 ? chars[i - 1].charCodeAt(0) : null;
                const isPrevConnected = prevCode && canConnectNext(prevCode);

                let ligature = null;
                if (nextCode === 0x0622) ligature = isPrevConnected ? 0xFEF6 : 0xFEF5; // لآ
                else if (nextCode === 0x0623) ligature = isPrevConnected ? 0xFEF8 : 0xFEF7; // لأ
                else if (nextCode === 0x0625) ligature = isPrevConnected ? 0xFEFA : 0xFEF9; // لإ
                else if (nextCode === 0x0627) ligature = isPrevConnected ? 0xFEFC : 0xFEFB; // لا

                if (ligature) {
                    result.push(String.fromCharCode(ligature));
                    i += 2;
                    continue;
                }
            }

            const prevCode = i > 0 ? chars[i - 1].charCodeAt(0) : null;
            const nextCode = i + 1 < len ? chars[i + 1].charCodeAt(0) : null;

            const connectPrev = prevCode && canConnectNext(prevCode);
            const connectNext = nextCode && canConnectPrev(nextCode) && !RIGHT_CONNECTING_ONLY.has(code);

            let formIndex = 0;
            if (connectPrev && connectNext) {
                formIndex = 3; // Medial
            } else if (connectPrev) {
                formIndex = 1; // Final
            } else if (connectNext) {
                formIndex = 2; // Initial
            } else {
                formIndex = 0; // Isolated
            }

            const shapedCode = ARABIC_GLYPHS[code][formIndex] || code;
            result.push(String.fromCharCode(shapedCode));
            i++;
        }

        return result.join('');
    }

    // Bidirectional processing for terminal stream data
    function bidiProcess(text) {
        if (!text || typeof text !== 'string') return text;
        
        // Fast test for Arabic characters
        if (!/[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]/.test(text)) {
            return text;
        }

        // Split text while preserving ANSI escape sequences
        const ansiRegex = /(\x1b\[[0-9;?]*[a-zA-Z]|\x1b\([a-zA-Z]|\x1b\].*?(\x07|\x1b\\))/g;
        const parts = [];
        let lastIdx = 0;
        let match;

        while ((match = ansiRegex.exec(text)) !== null) {
            if (match.index > lastIdx) {
                parts.push({ type: 'text', content: text.slice(lastIdx, match.index) });
            }
            parts.push({ type: 'ansi', content: match[0] });
            lastIdx = ansiRegex.lastIndex;
        }
        if (lastIdx < text.length) {
            parts.push({ type: 'text', content: text.slice(lastIdx) });
        }

        // Process only textual chunks, targeting only contiguous Arabic words
        const arabicWordRegex = /[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+/g;

        return parts.map(part => {
            if (part.type === 'ansi') return part.content;

            return part.content.replace(arabicWordRegex, (arabicWord) => {
                const shaped = reshapeWord(arabicWord);
                // Reverse characters within the word so it reads right-to-left in LTR grid
                return Array.from(shaped).reverse().join('');
            });
        }).join('');
    }

    return {
        reshape: reshapeWord,
        process: bidiProcess,
        isArabic: isArabicChar
    };
}));
