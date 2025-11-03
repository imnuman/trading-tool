# Collaboration Notes

## Current Setup

- **West Side:** Claude AI connected to GitHub repo
- **East Side:** Cursor AI (Auto) working on local codebase
- **Repository:** `git@github.com:imnuman/trading-tool.git`
- **Branch:** `main`

## Codebase Status

**Last Updated:** 2025-11-02

**Completion:** ~90%

### Completed Features:
- ✅ Core infrastructure (data fetching, strategy generation, backtesting)
- ✅ Train/test split (prevents overfitting)
- ✅ Regime detection
- ✅ Multi-timeframe confirmation
- ✅ Trend filter
- ✅ Economic calendar (news filter)
- ✅ Correlation manager
- ✅ Telegram bot interface
- ✅ Learning loop framework

### Critical Bugs Fixed:
- ✅ Stop loss sizes (15-30 pips, was 100-300)
- ✅ Pair names (EURUSD, was USD)
- ✅ Train/test split implementation
- ✅ Import errors fixed

### Ready for Testing:
1. Run `python3 scripts/pre_deploy.py` (generates strategies)
2. Run `python3 main.py` (starts Telegram bot)
3. Test commands: `/signal`, `/chart`, `/stats`

## Important Files

- `STATUS.md` - Complete component inventory
- `ROADMAP.md` - Development roadmap with priorities
- `TESTING.md` - Testing procedures
- `ACCOUNTS_AND_SERVICES.md` - Required accounts/services guide

## Notes for Collaboration

- All code is synced via GitHub
- Both sides working on same `main` branch
- Current focus: Complete critical features, test end-to-end
- System expected win rate: 58-65% (with all filters)

---

**Keep both sides updated on any major changes!**

