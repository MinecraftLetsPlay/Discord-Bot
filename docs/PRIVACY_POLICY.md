# Privacy Policy - MCLP Discord Bot

**Last Updated:** January 4, 2026  
**Effective Date:** January 4, 2026  
**Version:** 1.2 - Updated with complete feature overview

## 1. Data Controller

Dennis Plischke  
Discord Server: MCLP (MinecraftLetsPlay)  
Location: Germany 🇩🇪

---

## 2. Introduction

The MCLP Discord Bot ("Bot") is a comprehensive Discord application providing:
- Music streaming and playback
- Games and entertainment
- Utility tools (weather, reminders, polls, downloads)
- Moderation and server management
- Science and astronomy data
- Minecraft server integration
- System administration

This privacy policy explains how we collect, use, store, and protect your data under DSGVO/GDPR compliance.

---

## 3. What Data We Collect

### 3.1 Automatically Collected Data (Standard Logging)

When you use the Bot, we collect:

- **User IDs** (Discord unique identifier, NOT your username)
- **Guild IDs** (Server identifiers)
- **Channel IDs** (Channel identifiers)
- **Command Names** (Which commands executed, NOT parameters)
- **Timestamps** (When commands were executed)
- **Error Messages** (For debugging purposes only)

**Example:** When you type `!weather London`:
- Logged: User ID, Guild ID, Channel ID, Command "!weather"
- NOT Logged: "London" or any message content

### 3.2 Data We Do NOT Collect (Standard Mode)

The Bot **explicitly does NOT** collect or log:

- Your username or display name
- Your avatar or profile picture
- Message content from Direct Messages (DMs)
- Message content from server channels
- Email addresses or personal information
- IP addresses or device information
- Location data
- Browsing history or metadata

### 3.3 Special Mode: Debug Logging

When Debug Mode is activated (Global Whitelist Only):

**Who can activate:** Bot owner (Dennis Plischke) and Co-developer (Robin Stiller)

**What gets logged additionally:**
- Full message content (including text)
- Usernames (NOT user IDs, actual names)
- Detailed parameter values
- Command arguments

**Important Disclaimers:**
- Debug Mode is temporary and intended for technical troubleshooting
- Debug logs are deleted after 14 days (same as normal logs)
- Only used in controlled environment
- Gets disabled after debugging

### 3.4 Configuration Data Stored

The Bot stores local configuration files:

**Global Configuration (config.json):**
- Debug Mode status
- Bot status and activity
- Global whitelist (User IDs)
- Download folder paths
- Log file location
- Logging activation status

**Server-Specific Configuration (per_guild/{guild_id}.json):**
- Server whitelist (User IDs)
- Logging settings (enabled/disabled)
- Enabled/disabled logging channels
- Rules channel name
- Server-specific bot settings

**Special Data Files:**
- `reactionrole.json` - Message IDs, Channel IDs, Role IDs for reaction roles
- `hangman.json` - Word lists for hangman game
- `quiz.json` - Quiz questions and answers

**None of these files contain personal message content or usernames.**

### 3.5 Music Feature Data

When using music commands (!play, !pause, etc.):

**What we store:**
- YouTube video IDs (from search)
- Video titles and durations
- Queue order

**What we don't store:**
- Your search history
- Your listening preferences
- Personal recommendations

**External Service (yt-dlp/YouTube):**
- The Bot uses `yt-dlp` to query YouTube
- YouTube receives your search query
- Your IP may be visible to YouTube
- See YouTube's Privacy Policy for their practices

---

## 4. How We Use Your Data

Your data is used only for:

- Executing commands you request
- System logging and error tracking
- Improving bot stability and performance
- Security and moderation (preventing abuse/spam)
- Debugging technical issues (Debug Mode only)
- Reaction role assignments

Your data is **NOT** used for:

- Marketing or advertising
- Third-party sharing
- Profiling or behavioral analysis
- Commercial purposes
- Selling or trading with other services

---
## 5. Legal Basis for Data Processing (DSGVO Article 6)

Under German and EU data protection law (DSGVO), we can only process your personal data if we have a legal basis. Here are ours:

### Article 6(1)(b) DSGVO - Performance of a Contract

**What:** When you use the Bot, you enter an implicit contract.

**Why we process:** To fulfill this contract by:
- Processing your commands
- Storing your configurations
- Executing requested actions (reminders, music, games, etc.)

**Duration:** As long as you use the Bot and for 14 days after

### Article 6(1)(f) DSGVO - Legitimate Interests

**What:** We have a legitimate interest in:
- Security and abuse prevention (blocking hackers, spam bots)
- System stability (monitoring errors, performance)
- Legal compliance (documenting usage for disputes)
- Service improvement (understanding which features work)

**Why this is legitimate:** Your interests don't override ours because:
- We don't profile or make decisions about you
- We only store anonymous command names and IDs
- We delete data after 14 days
- We don't use data for marketing or targeting

**Your right:** You can object to this processing at any time (see Article 21 in Section 7).

### What This Means for You

- We have legal permission to log your commands
- We have legal permission to detect abuse
- We cannot use this data for purposes beyond what's stated
- You have rights to object, access, or delete your data

---
## 5. Data Storage and Security

### 5.1 Storage Location

**Primary Location:** Germany 🇩🇪

**Storage Method:** Local JSON files on German server (Raspberry Pi)

**Access Control:**
Only Dennis Plischke and Robin Stiller (Co-developer) have access to the server.
- Direct access via keyboard, mouse, and monitor
- Remote tunnel access secured by Cloudflare Zero Trust and Cloudflare Access

**Server-Level Security Measures:**

1. **Firewall Protection:**
   - UFW (Uncomplicated Firewall) installed and active
   - All inbound ports blocked by default
   - Only necessary ports explicitly opened
   - Outbound traffic restricted where possible

2. **Access Control:**
   - Linux default user account disabled
   - Login only possible with dedicated user account
   - 16-character minimum password requirement
   - Password includes uppercase, lowercase, numbers, and special characters
   - SSH key-based authentication preferred where applicable

3. **Intrusion Protection:**
   - Fail2Ban installed and active
   - Failed login attempts automatically blocked
   - Temporary IP bans for repeated failures
   - Monitoring of suspicious activity patterns

4. **Process Isolation:**
   - Bot process runs without sudo/root privileges
   - Bot runs in isolated Python virtual environment (venv)
   - Process has minimal required permissions
   - Strict file permissions (600/644) on all data files

5. **File Protection:**
   - Files not encrypted at rest but protected by:
     - Server file system permissions
     - Access restricted to bot process and authorized administrators only
   - No cloud synchronization
   - No automatic backups (only local logs with 14-day rotation)

**Encryption:**
- Data files not encrypted at rest (acceptable for local JSON logs)
- All remote access via Cloudflare Zero Trust uses TLS encryption
- SSH connections use encrypted protocols

**Summary of Security Layers:**
```
1. Firewall (UFW) - Network level
2. Fail2Ban - Login attempt blocking
3. Strong authentication - Account level
4. Process isolation - Application level
5. File permissions - Data level
6. Cloudflare Zero Trust - Remote access
```

### 5.2 Data Retention Schedule

**Automatic Deletion (14 Days):**
- All command logs deleted after 14 days
- Debug logs deleted after 14 days
- Old rotation logs purged automatically
- No manual intervention required

**Configuration Data Retention:**
- Server configs kept indefinitely (needed for operation)
- Can be deleted via `/logging off` or server deletion
- Reaction role data kept until manually removed
- Quiz/Hangman data kept for game functionality

### 5.3 Security Measures

- Access restricted to bot process and developer
- No cloud synchronization
- No third-party storage providers
- Local file-based with atomic read/write operations
- Rate limiting to prevent abuse
- Input validation on all commands
- No SQL databases (JSON only, prevents injection)

### 5.4 Potential Vulnerabilities & Mitigations

**Risk:** Server compromise
- **Mitigation:** Only runs on trusted German server

**Risk:** Accidental data exposure
- **Mitigation:** 14-day auto-deletion limits damage

**Risk:** Developer key compromise
- **Mitigation:** No sensitive data in logs

---

## 6. Third-Party Services

The Bot integrates with these external APIs:

### 6.1 NASA API
- **Purpose:** Astronomy features (!apod, !marsphoto, !asteroids, !sun, !exoplanet)
- **Data Sent:** Only API key (no personal data)
- **Rate Limit:** 5 requests/minute
- **Privacy:** See NASA's privacy policy

### 6.2 OpenWeatherMap API
- **Purpose:** Weather and city information (!weather, !city, !time)
- **Data Sent:** Location name only (no personal data)
- **Rate Limit:** 10 requests/minute
- **Privacy:** See OpenWeatherMap's privacy policy

### 6.3 Dictionary API (Free Dictionary)
- **Purpose:** Word definitions
- **Data Sent:** Word to define only
- **Rate Limit:** 20 requests/minute
- **Privacy:** API is open and free

### 6.4 CatFact API
- **Purpose:** Random cat facts (!catfact)
- **Data Sent:** None (generic request)
- **Rate Limit:** 30 requests/minute
- **Privacy:** See catfact.ninja privacy policy

### 6.5 YouTube/yt-dlp (Music Feature)
- **Purpose:** Music streaming and playback (!play, !join, etc.)
- **Data Sent:** Search queries, video IDs
- **Privacy:** YouTube can see your searches
- **Note:** Uses yt-dlp library (open source alternative)
- **Compliance:** Your responsibility to respect YouTube ToS

---

## 7. Your Rights (DSGVO Articles 15-22)

### Article 15: Right of Access
You have the right to know what personal data we hold about you.

**To request:**
- Contact bot owner via Discord
- Provide your User ID
- Will receive data within 30 days

### Article 16: Right to Rectification
You have the right to correct inaccurate data.

**Process:**
- Limited applicability (we only store IDs and commands)
- Contact bot owner for corrections

### Article 17: Right to Erasure ("Right to be Forgotten")
You have the right to request deletion of your data.

**What gets deleted:**
- All log entries mentioning your User ID
- Your server whitelists/configurations
- Your reminder data
- Your poll votes

**What doesn't get deleted:**
- Quiz answers already submitted (game functionality)
- Reaction role assignments (unless you leave server)

**Timeframe:** 7 days of request

### Article 18: Right to Restrict Processing
You can request that we stop processing your data.

**Effect:**
- Bot won't log your commands
- Can still use the bot (no command execution)
- Use `/logging off` per server

### Article 19: Right to Data Portability
You have the right to receive your data in machine-readable format.

**Available as:**
- JSON export of your configs
- Text file of your command history

### Article 21: Right to Object
You can object to data processing.

**To exercise your right:**
1. Contact bot owner via Discord
2. Specify which processing you object to
3. We'll cease processing within 14 days

### To Exercise Your Rights

**Contact Method:**
- Discord DM to: Bot Owner (Dennis Plischke)
- E-Mail to: dennisplischke755@gmail.com
- Include: Your User ID, Request Type, Details

**Response Time:** Within 30 days of request (DSGVO requirement)

**Verification:** We may ask for verification that you're the User ID owner

---

## 8. Rate Limiting & Performance Protection

To prevent abuse and ensure fair service:

**API Rate Limits:**
- NASA API: 5 requests/minute per user
- OpenWeatherMap: 10 requests/minute per user
- Dictionary: 20 requests/minute per user
- CatFact: 30 requests/minute per user

**Command Cooldowns:**
- Quiz: 10 seconds
- Hangman: 15 seconds
- Weather/City/Time: 8 seconds
- Calculation: 2 seconds
- Music: 10-15 seconds

**DoS Protection:**
- Calculator expression length limited to 500 chars
- Expression complexity checked
- Timeout protection (5 seconds max)
- No recursive expression evaluation

---

## 9. Data Breach & Incident Response

### Notification Process

In the unlikely event of a security incident:

1. **Immediate Actions:**
   - Isolate affected systems
   - Determine scope of breach
   - Begin investigation

2. **User Notification:**
   - Users affected will be notified via Discord
   - Notification within 72 hours of discovery
   - Details of what data was exposed

3. **Authorities:**
   - German data protection authorities informed if required
   - Documentation maintained for regulatory review

### Historical Security

As of January 2026: No security breaches reported

---

## 10. Data Protection Officer & Contact

**Data Controller:**
Dennis Plischke  
Germany 🇩🇪

**Contact Methods for Privacy Inquiries:**

You can reach out for:
- Data access requests (DSGVO Article 15)
- Deletion requests (DSGVO Article 17)
- Complaints about data processing
- General privacy questions

**Primary Contact (Discord):**
- Discord Username: @MinecraftLetsPlay2912
- Type `/dsgvo` in-bot for privacy information
- Direct Message to bot owner

**Alternative Contacts:**
- E-Mail: dennisplischke755@gmail.com
- GitHub Issues: https://github.com/MinecraftLetsPlay/Discord-Bot/issues (if repository is public)
- Response time: Within 30 days (DSGVO legal requirement)

**Data Subject Access:**
- Include your User ID in requests
- Briefly describe what you're requesting
- We may ask for verification

**Important:** This is a hobby bot run by one person. While we respond as quickly as possible, allow up to 14 days for processing during busy times.

---

## 11. Changes to This Policy

We review and update this policy:
- Every 6 months minimum
- When major features are added
- When data handling changes
- When legal requirements change

### How You'll Be Notified

**Major Changes** (Significant changes to your rights or data handling):
- Will be announced in Discord bot status
- Posted in MCLP server announcements
- Effective after 30 days notice

**Minor Changes** (Clarifications, formatting, minor additions):
- Updated on GitHub without advance notice
- Effective immediately

### Your Rights When We Change Terms

- Right to withdraw consent and stop using Bot
- Right to request deletion of data before accepting changes
- Continued use of Bot = acceptance of new policy
- Right to review version history (GitHub)

### Version History

- **v1.0** → Initial policy
- **v1.1** → Added complete feature overview, Art. 6 DSGVO basis, contact procedures (January 4, 2026)
- **v1.2** → Added more contact methods and corrected some information. Described security measures.

---

## Appendix A: Complete Data Categories

| Data Type       | Collected | Logged          | Retained       | Purpose               |
|-----------------|-----------|-----------------|----------------|-----------------------|
| User ID         |    YES    |       YES       |    14 days     | Command tracking      |
| Username        |    NO     | NO (debug: YES) |      N/A       | Privacy protection    |
| Guild ID        |    YES    |       YES       |    14 days     | Server identification |
| Channel ID      |    YES    |       YES       |    14 days     | Context for logs      |
| Command Name    |    YES    |       YES       |    14 days     | Usage tracking        |
| Command Args    |    NO     | NO (debug: YES) |      N/A       | Privacy protection    |
| Message Content |    NO     | NO (debug: YES) |      N/A       | Privacy protection    |
| DM Content      |    NO     |       NO        |      N/A       | Never logged          |
| Timestamps      |    YES    |       YES       |    14 days     | When events occurred  |
| Config Data     |    YES    |       NO        | Until deletion | Server/User settings  |
| API Responses   |  Minimal  |      NO         |     N/A        | Service-specific      |

---

## Appendix B: FAQ

**Q: Do you sell my data?**
A: Absolutely not. We have no commercial use for your data.

**Q: Can I opt-out of logging?**
A: Yes, use `/logging off` to disable logging per server.

**Q: How do I delete my data?**
A: Submit a data deletion request to the bot owner.

**Q: Is my music history logged?**
A: No. Music playback doesn't create logs.

**Q: What if I disagree with this policy?**
A: You can stop using the Bot anytime. Your data will be deleted after 14 days.

---

**Version:** 1.2
**Status:** Active  
**Language:** English (German equivalent available upon request)  
**Last Updated:** January 4, 2026  
**Compliance:** DSGVO/GDPR Article 13 & 14
