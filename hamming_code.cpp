/*
 * Hamming Code — Error Detection & Correction
 * ============================================
 * Message   : 1010101000011010  (16 data bits)
 * Parity    : 5 bits  (positions 1,2,4,8,16)
 * Codeword  : 21 bits
 *
 * Parity bit rule  : even parity (XOR of covered positions = 0)
 * Bit numbering    : starts at 1 (left = MSB of codeword)
 */

#include <iostream>
#include <vector>
#include <string>
#include <cmath>

// ─────────────────────────────────────────────────────────────────────────────
// Utility helpers
// ─────────────────────────────────────────────────────────────────────────────

bool isPowerOfTwo(int n) {
    return (n > 0) && ((n & (n - 1)) == 0);
}

void printBits(const std::vector<int>& bits, const std::string& label) {
    std::cout << label << " : ";
    for (int b : bits) std::cout << b;
    std::cout << "  (" << bits.size() << " bits)\n";
}

// ─────────────────────────────────────────────────────────────────────────────
// Step 1 – calculate required parity bits
//   2^r >= r + n + 1
// ─────────────────────────────────────────────────────────────────────────────

int calcParityBits(int n) {
    int r = 0;
    while ((1 << r) < (r + n + 1)) r++;
    return r;
}

// ─────────────────────────────────────────────────────────────────────────────
// Step 2 – encode: insert parity bits and compute their values
// ─────────────────────────────────────────────────────────────────────────────

std::vector<int> encode(const std::vector<int>& data) {
    int n = data.size();
    int r = calcParityBits(n);
    int total = n + r;

    std::vector<int> codeword(total + 1, 0);   // 1-indexed

    // Place data bits into non-power-of-two positions
    int dataIdx = 0;
    for (int i = 1; i <= total; i++) {
        if (!isPowerOfTwo(i)) {
            codeword[i] = data[dataIdx++];
        }
    }

    // Compute each parity bit (even parity via XOR)
    for (int i = 0; i < r; i++) {
        int parityPos = (1 << i);          // 1, 2, 4, 8, 16 ...
        int xorSum = 0;
        for (int j = parityPos; j <= total; j++) {
            if (j & parityPos)             // position j is covered by this parity bit
                xorSum ^= codeword[j];
        }
        codeword[parityPos] = xorSum;
    }

    // Return as 0-indexed vector (drop index-0 placeholder)
    std::vector<int> result(codeword.begin() + 1, codeword.end());
    return result;
}

// ─────────────────────────────────────────────────────────────────────────────
// Step 3 – verify / detect & correct a single-bit error
//   Compute syndrome = XOR of positions of all '1' bits
//   syndrome == 0  → no error
//   syndrome != 0  → error at that bit position
// ─────────────────────────────────────────────────────────────────────────────

int detectAndCorrect(std::vector<int>& received) {
    int total = received.size();
    int syndrome = 0;

    for (int i = 0; i < total; i++) {
        if (received[i] == 1)
            syndrome ^= (i + 1);           // positions are 1-indexed
    }
    return syndrome;                       // 0 = valid, else = error position (1-indexed)
}

// ─────────────────────────────────────────────────────────────────────────────
// Extract original data bits from codeword
// ─────────────────────────────────────────────────────────────────────────────

std::vector<int> extractData(const std::vector<int>& codeword) {
    std::vector<int> data;
    for (int i = 0; i < (int)codeword.size(); i++) {
        if (!isPowerOfTwo(i + 1))          // skip parity positions
            data.push_back(codeword[i]);
    }
    return data;
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

int main() {
    // ── Input message ────────────────────────────────────────────────────────
    std::string msg = "1010101000011010";
    std::vector<int> data;
    for (char c : msg) data.push_back(c - '0');

    std::cout << "\n╔══════════════════════════════════════════════╗\n";
    std::cout <<   "║         Hamming Code  —  Encoder / Decoder   ║\n";
    std::cout <<   "╚══════════════════════════════════════════════╝\n\n";

    int r = calcParityBits(data.size());
    std::cout << "Data bits    (n) : " << data.size() << "\n";
    std::cout << "Parity bits  (r) : " << r
              << "   [2^" << r << "=" << (1<<r)
              << " >= " << r << "+" << data.size() << "+1=" << r+data.size()+1 << "]\n";
    std::cout << "Codeword length  : " << data.size() + r << " bits\n\n";

    // ── Part A: Encoding ─────────────────────────────────────────────────────
    std::cout << "━━━━━━━━━━━━━━━━  PART A — ENCODING  ━━━━━━━━━━━━━━━━\n\n";

    printBits(data, "Original data  ");

    std::vector<int> codeword = encode(data);
    printBits(codeword, "Encoded codeword");

    // Show parity bit positions
    std::cout << "\nParity bit positions (1-indexed): ";
    for (int i = 0; i < r; i++) std::cout << (1 << i) << " ";
    std::cout << "\n";

    std::cout << "\nPosition : ";
    for (int i = 1; i <= (int)codeword.size(); i++)
        std::cout << (i < 10 ? " " : "") << i << " ";
    std::cout << "\n";

    std::cout << "Bit      : ";
    for (int b : codeword) std::cout << " " << b << " ";
    std::cout << "\n";

    std::cout << "Type     : ";
    for (int i = 1; i <= (int)codeword.size(); i++)
        std::cout << (isPowerOfTwo(i) ? " P " : " D ");
    std::cout << "\n";

    // ── Part B: Verification — no error ──────────────────────────────────────
    std::cout << "\n━━━━━━━━━━━━━━━  PART B — VERIFICATION  ━━━━━━━━━━━━━━━\n\n";

    std::cout << "[ Scenario 1 ]  Frame received without error\n";
    std::vector<int> received1 = codeword;
    printBits(received1, "Received       ");

    int syndrome1 = detectAndCorrect(received1);
    std::cout << "Syndrome       : " << syndrome1 << "\n";
    std::cout << "Decision       : "
              << (syndrome1 == 0 ? "ACCEPT — no error detected" : "ERROR") << "\n";

    std::vector<int> decoded1 = extractData(received1);
    printBits(decoded1, "Decoded data   ");

    // ── Part B: Verification — with a single-bit error ────────────────────
    std::cout << "\n[ Scenario 2 ]  Single-bit error injected at position 7\n";
    std::vector<int> received2 = codeword;
    int errorPos = 7;                      // 1-indexed
    received2[errorPos - 1] ^= 1;         // flip the bit

    printBits(received2, "Received       ");

    int syndrome2 = detectAndCorrect(received2);
    std::cout << "Syndrome       : " << syndrome2 << "\n";

    if (syndrome2 == 0) {
        std::cout << "Decision       : ACCEPT — no error detected\n";
    } else {
        std::cout << "Decision       : ERROR at bit position " << syndrome2 << "\n";
        // Correct the bit
        received2[syndrome2 - 1] ^= 1;
        std::cout << "Corrected bit  : position " << syndrome2 << " flipped back\n";
        printBits(received2, "Corrected frame");
    }

    std::vector<int> decoded2 = extractData(received2);
    printBits(decoded2, "Decoded data   ");

    std::cout << "\n";
    return 0;
}
