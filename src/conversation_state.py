"""
Conversation Memory and State — Exercise 1.3

Tracks interactions across time and channels for each customer:
- Ongoing conversation sessions (per customer, keyed by email)
- Sentiment trajectory (is the interaction going well?)
- Topics discussed per turn (for reporting)
- Resolution status (solved/pending/escalated)
- Original channel and any cross-channel switches
- Customer identity (email as primary key)
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


# ── Conversation Session ──────────────────────────────────────────────────────

SESSION_TIMEOUT = timedelta(hours=1)


@dataclass
class ConversationTurn:
    """A single exchange in the conversation."""
    timestamp: str
    channel: str
    message_sent: str          # customer's message
    reply_sent: str            # agent's reply
    topic_detected: str        # category of this turn
    sentiment_score: float     # sentiment for this turn
    escalated: bool            # did we escalate this turn?
    resolved: bool             # was this turn resolved?


@dataclass
class CustomerProfile:
    """Persistent customer identity across conversations."""
    customer_email: str
    customer_name: str = ""
    phone: str = ""
    company: str = ""
    plan: str = "free"
    total_conversations: int = 0
    total_tickets: int = 0
    escalations_total: int = 0
    resolutions_total: int = 0
    last_seen: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class ConversationSession:
    """
    A running conversation with a customer.
    A new session is created after a period of inactivity.
    """

    session_id: str
    customer_email: str       # primary identifier
    customer_name: str = ""
    customer_profile: Optional[CustomerProfile] = None

    original_channel: str = ""       # channel the session started on
    current_channel: str = ""        # latest channel used
    channel_history: list = field(default_factory=list)  # all channels used

    topic_history: list = field(default_factory=list)    # categories seen this session
    sentiment_track: list = field(default_factory=list)  # sentiment scores over time
    turns: list = field(default_factory=list)            # full turn history

    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    resolved: bool = False
    escalated: bool = False
    escalation_queue: str = ""

    summary: str = ""            # auto-generated summary of topics discussed
    tags: list = field(default_factory=list)  # high-level tags for reporting

    @property
    def channel_switched(self) -> bool:
        """Has the customer switched channels during this conversation?"""
        return len(set(self.channel_history)) > 1

    @property
    def avg_sentiment(self) -> float:
        """Average sentiment across this conversation."""
        if not self.sentiment_track:
            return 0.0
        return sum(self.sentiment_track) / len(self.sentiment_track)

    @property
    def sentiment_trend(self) -> float:
        """Sentiment direction: positive = improving, negative = worsening."""
        if len(self.sentiment_track) < 2:
            return 0.0
        # Compare first half avg to second half avg
        mid = len(self.sentiment_track) // 2
        first_avg = sum(self.sentiment_track[:mid]) / mid
        second_avg = sum(self.sentiment_track[mid:]) / (len(self.sentiment_track) - mid)
        return round(second_avg - first_avg, 3)

    @property
    def is_timed_out(self) -> bool:
        return datetime.now(timezone.utc) - self.last_activity > SESSION_TIMEOUT

    @property
    def report_summary(self) -> dict:
        """Summary dict for reporting and analytics."""
        return {
            "session_id": self.session_id,
            "customer_email": self.customer_email,
            "customer_name": self.customer_name,
            "original_channel": self.original_channel,
            "channels_used": list(set(self.channel_history)),
            "channel_switched": self.channel_switched,
            "turns": len(self.turns),
            "topics": self.topic_history,
            "avg_sentiment": round(self.avg_sentiment, 3),
            "sentiment_trend": self.sentiment_trend,
            "resolved": self.resolved,
            "escalated": self.escalated,
            "escalation_queue": self.escalation_queue,
            "started_at": self.started_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }

    def add_turn(self, turn: ConversationTurn):
        """Record a new conversation turn and update state."""
        self.turns.append(turn)
        self.sentiment_track.append(turn.sentiment_score)
        self.channel_history.append(turn.channel)
        self.current_channel = turn.channel

        if turn.topic_detected and turn.topic_detected not in self.topic_history:
            self.topic_history.append(turn.topic_detected)

        if turn.escalated:
            self.escalated = True
            self.escalation_queue = turn.topic_detected  # will be overwritten if set separately

        if turn.resolved:
            self.resolved = True

        self.last_activity = datetime.now(timezone.utc)

    def update_resolution(self, resolved: bool, escalated: bool = False, escalation_queue: str = ""):
        """Manually update resolution state."""
        self.resolved = resolved
        self.escalated = escalated
        if escalated and escalation_queue:
            self.escalation_queue = escalation_queue

    def close(self, summary: str = ""):
        """Mark the conversation as closed."""
        self.resolved = True
        self.summary = summary
        self.last_activity = datetime.now(timezone.utc)


# ── Conversation Memory Manager ──────────────────────────────────────────────

class ConversationMemory:
    """
    Thread-safe manager for all customer conversations.
    Uses email as primary key for customer identity.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # email → active session
        self._active_sessions: dict[str, ConversationSession] = {}
        # email → all completed sessions
        self._history: dict[str, list[ConversationSession]] = {}
        # email → customer profile
        self._customers: dict[str, CustomerProfile] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SESSION-{self._counter:04d}"

    def get_or_create_profile(self, email: str, name: str = "", phone: str = "", company: str = "", plan: str = "free") -> CustomerProfile:
        """Get or create a customer profile."""
        with self._lock:
            if email not in self._customers:
                self._customers[email] = CustomerProfile(
                    customer_email=email,
                    customer_name=name,
                    phone=phone,
                    company=company,
                    plan=plan,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            profile = self._customers[email]
            if name:
                profile.customer_name = name
            if phone:
                profile.phone = phone
            if company:
                profile.company = company
            if plan != "free":
                profile.plan = plan
            return profile

    def get_profile(self, email: str) -> Optional[CustomerProfile]:
        """Look up a customer profile by email."""
        with self._lock:
            return self._customers.get(email)

    def get_active_session(self, email: str) -> Optional[ConversationSession]:
        """
        Get the active session for a customer.
        Returns None if no active session or timed out.
        """
        with self._lock:
            session = self._active_sessions.get(email)
            if session and not session.is_timed_out:
                return session
            # Timed out — move to history
            if session:
                self._history.setdefault(email, []).append(session)
                del self._active_sessions[email]
            return None

    def create_session(self, email: str, channel: str, name: str = "") -> ConversationSession:
        """Create a new conversation session for a customer."""
        with self._lock:
            # If there's a timed-out session, archive it
            old = self._active_sessions.get(email)
            if old:
                self._history.setdefault(email, []).append(old)

            session = ConversationSession(
                session_id=self._next_id(),
                customer_email=email,
                customer_name=name or self._customers.get(email, CustomerProfile(customer_email="")).customer_name,
                customer_profile=self._customers.get(email),
                original_channel=channel,
                current_channel=channel,
            )
            self._active_sessions[email] = session
            return session

    def get_customer_history(self, email: str) -> list[ConversationSession]:
        """All completed sessions for a customer."""
        with self._lock:
            sessions = self._history.get(email, [])
            return sessions

    def get_session_with_context(self, email: str) -> tuple[Optional[ConversationSession], str]:
        """
        Get active session and detect if channel switched.
        Returns (session, context_note) where context_note explains
        any channel switch or session timeout for the agent.
        """
        session = self.get_active_session(email)
        if not session:
            return None, "new_session"

        return session, ""

    def record_turn(
        self,
        session: ConversationSession,
        message_body: str,
        reply_body: str,
        channel: str,
        topic: str,
        sentiment: float,
        escalated: bool,
        resolved: bool,
    ) -> ConversationTurn:
        """Record a turn and return the turn object."""
        turn = ConversationTurn(
            timestamp=datetime.now(timezone.utc).isoformat(),
            channel=channel,
            message_sent=message_body,
            reply_sent=reply_body,
            topic_detected=topic,
            sentiment_score=sentiment,
            escalated=escalated,
            resolved=resolved,
        )
        session.add_turn(turn)
        self._update_customer_stats(session.customer_email, escalated, resolved)
        return turn

    def get_turn_history(self, session: ConversationSession) -> list[ConversationTurn]:
        """All turns in this session."""
        return session.turns

    def _update_customer_stats(self, email: str, escalated: bool, resolved: bool):
        """Update customer profile counters."""
        profile = self._customers.get(email)
        if profile:
            if resolved:
                profile.resolutions_total += 1
            if escalated:
                profile.escalations_total += 1
            profile.last_seen = datetime.now(timezone.utc).isoformat()
            profile.total_tickets += 1
