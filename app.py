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
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background — warm light gradient */
    .stApp {
        background: linear-gradient(150deg, #fdf4ff 0%, #f0f4ff 50%, #fff7ed 100%);
        min-height: 100vh;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(16px);
        border-right: 1px solid rgba(124, 58, 237, 0.12);
        box-shadow: 4px 0 24px rgba(124, 58, 237, 0.06);
    }

    /* Chat message user bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, #ede9fe, #ddd6fe);
        border-radius: 16px;
        border: 1px solid rgba(124, 58, 237, 0.2);
        padding: 8px;
        margin: 4px 0;
    }

    /* Chat message assistant bubble */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background: white;
        border-radius: 16px;
        border: 1px solid rgba(124, 58, 237, 0.1);
        box-shadow: 0 2px 12px rgba(124, 58, 237, 0.06);
        padding: 8px;
        margin: 4px 0;
    }

    /* Chat input */
    [data-testid="stChatInputTextArea"] {
        background: white !important;
        border: 1.5px solid rgba(124, 58, 237, 0.3) !important;
        border-radius: 12px !important;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 12px;
        border: 1px solid rgba(124, 58, 237, 0.12);
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.06);
    }

    /* Header */
    .main-header {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    .main-header h1 {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(90deg, #7c3aed, #f97316, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .main-header p {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 4px;
    }

    /* Divider */
    hr {
        border-color: rgba(124, 58, 237, 0.1);
    }

    /* Section headers in sidebar */
    h3 {
        color: #4c1d95 !important;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Provider Factory
# ============================================================
def create_provider(provider_name: str, model_name: str):
    """Khởi tạo LLM Provider theo lựa chọn."""
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
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = 0
    if "total_requests" not in st.session_state:
        st.session_state.total_requests = 0


# ============================================================
# Sidebar
# ============================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Cấu hình")
        st.markdown("---")

        # Provider selection
        provider = st.selectbox(
            "🤖 LLM Provider",
            options=["Gemini", "OpenAI"],
            index=0,
            help="Chọn mô hình ngôn ngữ để chạy Agent."
        )

        # Model selection based on provider
        if provider == "OpenAI":
            model = st.selectbox(
                "📦 Model",
                options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                index=0,
            )
        else:  # Gemini
            model = st.selectbox(
                "📦 Model",
                options=["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
                index=0,
            )

        max_steps = st.slider(
            "🔄 Max Steps (ReAct loops)",
            min_value=1, max_value=10, value=5, step=1,
            help="Số vòng lặp Thought-Action tối đa cho Agent."
        )

        st.markdown("---")

        # Init / Reset Agent
        if st.button("🚀 Khởi động / Reset Agent", use_container_width=True, type="primary"):
            with st.spinner("Đang khởi tạo Agent..."):
                llm = create_provider(provider, model)
                from src.agent.agent import ReActAgent
                st.session_state.agent = ReActAgent(llm=llm, max_steps=max_steps)
                st.session_state.messages = []
                st.session_state.total_tokens = 0
                st.session_state.total_requests = 0
            st.success(f"✅ Agent đã sẵn sàng! ({provider} / {model})")

        st.markdown("---")

        # Stats
        st.markdown("### 📊 Thống kê phiên")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tin nhắn", len(st.session_state.messages))
        with col2:
            st.metric("Yêu cầu", st.session_state.total_requests)
        st.metric("Tổng Tokens", st.session_state.total_tokens)

        st.markdown("---")

        # Available Tools
        st.markdown("### 🛠️ Công cụ của Agent")
        tools = [
            ("🔍", "search_restaurants", "Tìm quán theo tiêu chí"),
            ("📋", "get_restaurant_details", "Chi tiết nhà hàng"),
            ("⏰", "check_open_status", "Kiểm tra giờ mở cửa"),
            ("💰", "calculate_estimated_cost", "Tính chi phí nhóm"),
            ("🆘", "human_escalation_fallback", "Chuyển hỗ trợ thủ công"),
        ]
        for icon, name, desc in tools:
            st.markdown(f"{icon} **`{name}`**  \n<small style='color:rgba(255,255,255,0.5)'>{desc}</small>", unsafe_allow_html=True)

        st.markdown("---")

        # Quick test scenarios
        st.markdown("### 💡 Câu hỏi mẫu")
        samples = [
            "Tìm nhà hàng Pháp ở Tây Hồ, giá dưới 300k",
            "Quán 'Phở Đặc Biệt' còn mở lúc 22:00 không?",
            "Tôi 3 người, muốn ăn hải sản ở Hoàn Kiếm",
            "Tìm quán vegetarian rating cao nhất",
            "Nhóm 5 người ăn tại Hoa Sữa Restaurant hết bao nhiêu?",
        ]
        for s in samples:
            if st.button(f"💬 {s[:35]}...", key=s, use_container_width=True):
                st.session_state["pending_input"] = s

    return provider, model


# ============================================================
# Main Chat Area
# ============================================================
def render_chat():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🍜 Hanoi Food Expert</h1>
        <p>Trợ lý AI thông minh giúp bạn tìm nhà hàng ngon tại Hà Nội · Powered by ReAct Agent</p>
    </div>
    """, unsafe_allow_html=True)

    # Agent not initialized
    if st.session_state.agent is None:
        st.info("👈 Vui lòng chọn Provider và nhấn **Khởi động / Reset Agent** ở thanh bên để bắt đầu.", icon="ℹ️")
        st.markdown("---")
        st.markdown("""
        #### 🗺️ ReAct Agent hoạt động như thế nào?
        ```
        User Input
            ↓
        Thought (Agent suy nghĩ...)
            ↓
        Action (Gọi Tool: search_restaurants, check_open_status, ...)
            ↓
        Observation (Kết quả từ Tool)
            ↓ (lặp tối đa N lần)
        Final Answer ✅
        ```
        """)
        return

    # Display chat history
    for msg in st.session_state.messages:
        avatar = "🧑" if msg["role"] == "user" else "🍜"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Handle pending input from sidebar quick buttons
    pending = st.session_state.pop("pending_input", None)

    # Chat input
    user_input = st.chat_input("Bạn muốn tìm quán ăn nào? (VD: 'Tìm nhà hàng Pháp ở Tây Hồ giá rẻ')") or pending

    if user_input:
        # Show user message
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Run agent
        with st.chat_message("assistant", avatar="🍜"):
            with st.spinner("🤔 Agent đang suy nghĩ..."):
                try:
                    response = st.session_state.agent.run(user_input)
                    st.session_state.total_requests += 1
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    err_msg = f"❌ Có lỗi xảy ra: `{str(e)}`"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg})

        # Auto scroll trigger
        st.rerun()


# ============================================================
# Entry Point
# ============================================================
def main():
    init_session_state()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
