<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="chat-title">
        <span class="chat-icon">💬</span>
        <h2>智能对话助手</h2>
      </div>
      <button class="btn-clear" @click="clearChat">
        🗑️ 清空对话
      </button>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div class="welcome-message">
        <div class="avatar bot-avatar">🤖</div>
        <div class="message-content">
          <p>您好！我是您的智能对话助手。</p>
          <p>有什么我可以帮助您的吗？</p>
        </div>
      </div>
      
      <div 
        v-for="(msg, index) in messages" 
        :key="index"
        :class="['message-item', msg.role === 'user' ? 'user-message' : 'bot-message']"
      >
        <div :class="['avatar', msg.role === 'user' ? 'user-avatar' : 'bot-avatar']">
          {{ msg.role === 'user' ? '👤' : '🤖' }}
        </div>
        <div class="message-bubble">
          <p>{{ msg.content }}</p>
        </div>
      </div>

      <div v-if="isLoading" class="loading-indicator">
        <div class="avatar bot-avatar">🤖</div>
        <div class="loading-bubble">
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
          <span class="loading-dot"></span>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <textarea
        v-model="inputMessage"
        @keydown.enter.exact.prevent="sendMessage"
        placeholder="输入您的消息..."
        class="message-input"
        rows="2"
        ref="inputRef"
      ></textarea>
      <button 
        class="send-btn" 
        @click="sendMessage"
        :disabled="!inputMessage.trim() || isLoading"
      >
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { chatApi } from '../api'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)

const userId = ref('user_' + Date.now())

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  messages.value.push({ role: 'user', content: message })
  inputMessage.value = ''
  isLoading.value = true
  
  await scrollToBottom()

  try {
    const response = await chatApi.sendMessage(message, userId.value)
    if (response.data.success) {
      messages.value.push({ role: 'assistant', content: response.data.response })
    } else {
      messages.value.push({ role: 'assistant', content: '抱歉，我暂时无法回复您的消息。' })
    }
  } catch (error) {
    messages.value.push({ role: 'assistant', content: '网络连接出错，请稍后重试。' })
    console.error('Chat error:', error)
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

const clearChat = () => {
  messages.value = []
  inputMessage.value = ''
}

onMounted(() => {
  if (inputRef.value) {
    inputRef.value.focus()
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 136px);
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-dark-secondary) 100%);
  border-bottom: 1px solid rgba(212, 168, 75, 0.2);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #E8D5B7;
}

.chat-icon {
  font-size: 1.4rem;
}

.chat-title h2 {
  font-family: 'Noto Serif SC', serif;
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: 2px;
  margin: 0;
  color: var(--accent-light);
}

.btn-clear {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(212, 168, 75, 0.3);
  border-radius: var(--radius);
  color: #C4B49A;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s;
  font-family: inherit;
}

.btn-clear:hover {
  background: rgba(255, 255, 255, 0.15);
  color: var(--accent-light);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: linear-gradient(180deg, #FAF6F0 0%, #F5EDE0 100%);
}

.welcome-message {
  display: flex;
  gap: 12px;
  margin-bottom: 1.5rem;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 1rem;
  animation: messageFadeIn 0.3s ease;
}

@keyframes messageFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.user-avatar {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
}

.bot-avatar {
  background: linear-gradient(135deg, var(--jade-green), #3D8B6D);
}

.message-content, .message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  line-height: 1.7;
}

.message-content {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid var(--border);
}

.message-content p {
  margin: 0;
  color: var(--text);
  font-size: 0.95rem;
}

.message-content p:first-child {
  margin-bottom: 0.5rem;
}

.user-message .message-bubble {
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #FFF5E6;
  border-radius: var(--radius-lg) var(--radius-lg) 4px var(--radius-lg);
  margin-left: auto;
}

.bot-message .message-bubble {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) 4px;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-bubble p {
  margin: 0;
}

.bot-message .message-bubble p {
  margin: 0;
  color: var(--text);
  font-size: 0.95rem;
}

.loading-indicator {
  display: flex;
  gap: 12px;
}

.loading-bubble {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) 4px;
  padding: 12px 16px;
  display: flex;
  gap: 4px;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  animation: loadingPulse 1.4s infinite ease-in-out;
}

.loading-dot:nth-child(1) { animation-delay: 0s; }
.loading-dot:nth-child(2) { animation-delay: 0.2s; }
.loading-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes loadingPulse {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-area {
  display: flex;
  gap: 10px;
  padding: 1rem 1.5rem;
  background: white;
  border-top: 1px solid var(--border);
}

.message-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  font-family: inherit;
  resize: none;
  transition: all 0.3s;
  background: var(--bg);
  line-height: 1.5;
}

.message-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(139, 37, 0, 0.08);
}

.message-input::placeholder {
  color: var(--text-light);
}

.send-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--primary), var(--primary-dark));
  color: #FFF5E6;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  font-family: inherit;
  box-shadow: 0 2px 8px rgba(139, 37, 0, 0.25);
  white-space: nowrap;
}

.send-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 37, 0, 0.35);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .chat-container {
    height: calc(100vh - 180px);
  }
  
  .chat-header {
    padding: 0.75rem 1rem;
  }
  
  .chat-title h2 {
    font-size: 1.1rem;
  }
  
  .chat-messages {
    padding: 1rem;
  }
  
  .message-content, .message-bubble {
    max-width: 85%;
    padding: 10px 14px;
  }
  
  .chat-input-area {
    padding: 0.75rem 1rem;
    flex-direction: column;
  }
  
  .send-btn {
    align-self: flex-end;
  }
}
</style>