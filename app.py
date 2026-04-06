import os
import sys
import streamlit as st
from dotenv import load_dotenv

# --- Path Setup ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

# --- Page Config (MUST be first Streamlit command) ---
st.set_page_config(
    page_title="🍜 Hanoi Food Expert",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for premium light theme ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(150deg, #fdf4ff 0%, #f0f4ff 50%, #fff7ed 100%);
        min-height: 100vh;
    }

    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(124, 58, 237, 0.12);
        box-shadow: 4px 0 24px rgba(124, 58, 237, 0.06);
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, #ede9fe, #ddd6fe);
        border-radius: 16px;
        border: 1px solid rgba(124, 58, 237, 0.2);
        padding: 8px; margin: 4px 0;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: white;
        border-radius: 16px;
        border: 1px solid rgba(124, 58, 237, 0.1);
        box-shadow: 0 2px 12px rgba(124, 58, 237, 0.06);
        padding: 8px; margin: 4px 0;
    }

    [data-testid="stChatInputTextArea"] {
        background: white !important;
        border: 1.5px solid rgba(124, 58, 237, 0.3) !important;
        border-radius: 12px !important;
    }

    [data-testid="stMetric"] {
        background: white; border-radius: 12px; padding: 12px;
        border: 1px solid rgba(124, 58, 237, 0.12);
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.06);
    }

    .main-header { text-align: center; padding: 16px 0 8px 0; }
    .main-header h1 {
        font-size: 2.2rem; font-weight: 700;
        background: linear-gradient(90deg, #7c3aed, #f97316, #ec4899);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .main-header p { color: #6b7280; font-size: 0.9rem; margin-top: 4px; }

    /* Column header badges */
    .col-badge-agent {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white; border-radius: 12px; padding: 10px 16px;
        font-weight: 600; font-size: 0.95rem; text-align: center;
        margin-bottom: 8px; box-shadow: 0 4px 12px rgba(124,58,237,0.25);
    }
    .col-badge-chatbot {
        background: linear-gradient(135deg, #f97316, #ef4444);
        color: white; border-radius: 12px; padding: 10px 16px;
        font-weight: 600; font-size: 0.95rem; text-align: center;
        margin-bottom: 8px; box-shadow: 0 4px 12px rgba(249,115,22,0.25);
    }

    hr { border-color: rgba(124, 58, 237, 0.1); }
    h3 { color: #4c1d95 !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Provider Factory
# ============================================================
def create_provider(provider_name: str, model_name: str):
    if provider_name == "OpenAI":
        from src.core.openai_provider import OpenAIProvider
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ Chưa có OPENAI_API_KEY trong file .env!")
            st.stop()
        return OpenAIProvider(model_name=model_name, api_key=api_key)
    elif provider_name == "Gemini":
        from src.core.gemini_provider import GeminiProvider
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Chưa có GEMINI_API_KEY trong file .env!")
            st.stop()
        return GeminiProvider(model_name=model_name, api_key=api_key)
    else:
        st.error(f"Provider '{provider_name}' chưa được hỗ trợ.")
        st.stop()


# ============================================================
# Session State Initialization
# ============================================================
def init_session_state():
    defaults = {
        "agent": None,
        "chatbot": None,
        "agent_messages": [],
        "chatbot_messages": [],
        "total_requests": 0,
        "mode": "compare",  # "agent", "chatbot", "compare"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# Sidebar
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Cấu hình")
        st.markdown("---")

        # Mode selector
        mode = st.radio(
            "🖥️ Chế độ hiển thị",
            options=["🔀 So sánh", "🤖 Chỉ ReAct Agent", "💬 Chỉ Chatbot"],
            index=0,
            help="Chọn chế độ hiển thị giao diện."
        )
        mode_map = {"🔀 So sánh": "compare", "🤖 Chỉ ReAct Agent": "agent", "💬 Chỉ Chatbot": "chatbot"}
        st.session_state.mode = mode_map[mode]

        st.markdown("---")

        # Provider & Model
        provider = st.selectbox(
            "🤖 LLM Provider",
            options=["Gemini", "OpenAI"],
            index=0,
        )
        if provider == "OpenAI":
            model = st.selectbox("📦 Model", ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
        else:
            model = st.selectbox("📦 Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"])

        max_steps = st.slider("🔄 Max Steps (Agent)", 1, 10, 5, help="Số vòng lặp Thought-Action tối đa.")

        st.markdown("---")

        if st.button("🚀 Khởi động / Reset", use_container_width=True, type="primary"):
            with st.spinner("Đang khởi tạo..."):
                llm_agent = create_provider(provider, model)
                llm_chatbot = create_provider(provider, model)

                from src.agent.agent import ReActAgent
                from src.chatbot_baseline import BaselineChatbot

                st.session_state.agent = ReActAgent(llm=llm_agent, max_steps=max_steps)
                st.session_state.chatbot = BaselineChatbot(llm=llm_chatbot)
                st.session_state.agent_messages = []
                st.session_state.chatbot_messages = []
                st.session_state.total_requests = 0
            st.success(f"✅ Sẵn sàng! ({provider} / {model})")

        st.markdown("---")

        # Stats
        st.markdown("### 📊 Thống kê")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Agent msgs", len(st.session_state.agent_messages))
        with c2:
            st.metric("Bot msgs", len(st.session_state.chatbot_messages))
        st.metric("Tổng yêu cầu", st.session_state.total_requests)

        st.markdown("---")

        # Tools
        st.markdown("### 🛠️ Tools của Agent")
        for icon, name, desc in [
            ("🔍", "search_restaurants", "Tìm quán theo tiêu chí"),
            ("📋", "get_restaurant_details", "Chi tiết nhà hàng"),
            ("⏰", "check_open_status", "Kiểm tra giờ mở cửa"),
            ("💰", "calculate_estimated_cost", "Tính chi phí nhóm"),
            ("🆘", "human_escalation_fallback", "Chuyển hỗ trợ thủ công"),
        ]:
            st.markdown(f"{icon} **`{name}`**  \n<small style='color:#6b7280'>{desc}</small>", unsafe_allow_html=True)

        st.markdown("---")

        # Quick samples
        st.markdown("### 💡 Câu hỏi mẫu")
        samples = [
            "Tìm nhà hàng Pháp ở Tây Hồ, giá dưới 300k",
            "Quán 'Phở Đặc Biệt' còn mở lúc 22:00?",
            "Tôi 3 người, muốn ăn hải sản ở Hoàn Kiếm",
            "Tìm quán vegetarian rating cao nhất",
            "Nhóm 5 người ăn tại Hoa Sữa hết bao nhiêu?",
        ]
        for s in samples:
            label = s[:38] + "..." if len(s) > 38 else s
            if st.button(f"💬 {label}", key=f"sample_{s}", use_container_width=True):
                st.session_state["pending_input"] = s


# ============================================================
# Chat column renderer (reusable)
# ============================================================
def render_chat_column(col, label_html: str, messages_key: str, runner_key: str,
                        avatar: str, spinner_text: str, user_input: str | None):
    """Render một cột chat cho Agent hoặc Chatbot."""
    with col:
        st.markdown(label_html, unsafe_allow_html=True)

        # Scroll area — show history
        chat_container = st.container(height=480)
        with chat_container:
            for msg in st.session_state[messages_key]:
                role_avatar = "🧑" if msg["role"] == "user" else avatar
                with st.chat_message(msg["role"], avatar=role_avatar):
                    st.markdown(msg["content"])

        # Process new input
        if user_input and st.session_state[runner_key] is not None:
            with chat_container:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(user_input)
            st.session_state[messages_key].append({"role": "user", "content": user_input})

            with chat_container:
                with st.chat_message("assistant", avatar=avatar):
                    with st.spinner(spinner_text):
                        try:
                            response = st.session_state[runner_key].run(user_input)
                            st.markdown(response)
                            st.session_state[messages_key].append({"role": "assistant", "content": response})
                        except Exception as e:
                            err = f"❌ Lỗi: `{str(e)}`"
                            st.error(err)
                            st.session_state[messages_key].append({"role": "assistant", "content": err})


# ============================================================
# Main Chat Area
# ============================================================
def render_main():
    st.markdown("""
    <div class="main-header">
        <h1>🍜 Hanoi Food Expert</h1>
        <p>So sánh ReAct Agent vs Chatbot Baseline · Powered by Agentic AI</p>
    </div>
    """, unsafe_allow_html=True)

    not_ready = (st.session_state.agent is None and st.session_state.chatbot is None)
    if not_ready:
        st.info("👈 Chọn Provider và nhấn **🚀 Khởi động / Reset** ở thanh bên để bắt đầu.", icon="ℹ️")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            #### 🤖 ReAct Agent
            ```
            User Input → Thought → Action (Tool) → Observation → Final Answer
            ```
            Agent **tra cứu dữ liệu thật** từ database nhà hàng Hà Nội.
            """)
        with c2:
            st.markdown("""
            #### 💬 Chatbot Baseline
            ```
            User Input → LLM → Answer (chỉ dùng kiến thức sẵn có)
            ```
            Chatbot **không có tool**, dễ bịa thông tin nếu không biết.
            """)
        return

    # Handle pending input
    pending = st.session_state.pop("pending_input", None)

    mode = st.session_state.mode

    # ---- COMPARE MODE ----
    if mode == "compare":
        col_agent, col_bot = st.columns(2, gap="medium")

        badge_agent = '<div class="col-badge-agent">🤖 ReAct Agent &nbsp;·&nbsp; Có Tool</div>'
        badge_chatbot = '<div class="col-badge-chatbot">💬 Chatbot Baseline &nbsp;·&nbsp; Không Tool</div>'

        # Shared input at bottom (only in compare mode)
        user_input = st.chat_input("Nhập câu hỏi để so sánh cả 2 cùng lúc...") or pending

        if user_input:
            st.session_state.total_requests += 1

        render_chat_column(col_agent, badge_agent, "agent_messages", "agent",
                           "🤖", "🤔 Agent đang suy nghĩ...", user_input)
        render_chat_column(col_bot, badge_chatbot, "chatbot_messages", "chatbot",
                           "💬", "💭 Chatbot đang trả lời...", user_input)

        if user_input:
            st.rerun()

    # ---- AGENT ONLY ----
    elif mode == "agent":
        st.markdown('<div class="col-badge-agent">🤖 ReAct Agent &nbsp;·&nbsp; Có Tool</div>', unsafe_allow_html=True)
        user_input = st.chat_input("Hỏi Agent về nhà hàng Hà Nội...") or pending

        for msg in st.session_state.agent_messages:
            with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])

        if user_input and st.session_state.agent:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)
            st.session_state.agent_messages.append({"role": "user", "content": user_input})
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("🤔 Agent đang suy nghĩ..."):
                    try:
                        resp = st.session_state.agent.run(user_input)
                        st.markdown(resp)
                        st.session_state.agent_messages.append({"role": "assistant", "content": resp})
                        st.session_state.total_requests += 1
                    except Exception as e:
                        st.error(f"❌ {e}")
            st.rerun()

    # ---- CHATBOT ONLY ----
    elif mode == "chatbot":
        st.markdown('<div class="col-badge-chatbot">💬 Chatbot Baseline &nbsp;·&nbsp; Không Tool</div>', unsafe_allow_html=True)
        user_input = st.chat_input("Hỏi Chatbot về nhà hàng Hà Nội...") or pending

        for msg in st.session_state.chatbot_messages:
            with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "💬"):
                st.markdown(msg["content"])

        if user_input and st.session_state.chatbot:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)
            st.session_state.chatbot_messages.append({"role": "user", "content": user_input})
            with st.chat_message("assistant", avatar="💬"):
                with st.spinner("💭 Chatbot đang trả lời..."):
                    try:
                        resp = st.session_state.chatbot.run(user_input)
                        st.markdown(resp)
                        st.session_state.chatbot_messages.append({"role": "assistant", "content": resp})
                        st.session_state.total_requests += 1
                    except Exception as e:
                        st.error(f"❌ {e}")
            st.rerun()


# ============================================================
# Entry Point
# ============================================================
def main():
    init_session_state()
    render_sidebar()
    render_main()


if __name__ == "__main__":
    main()
