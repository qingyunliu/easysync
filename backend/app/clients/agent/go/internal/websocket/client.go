package websocket

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"easysync/agent/internal/log"
)

// Client WebSocket客户端
type Client struct {
	conn      *websocket.Conn
	url       string
	send      chan []byte
	handlers  map[string]MessageHandler
	mutex     sync.RWMutex
	ctx       context.Context
	cancel    context.CancelFunc
	connected bool
}

// MessageHandler 消息处理器类型
type MessageHandler func([]byte) error

// NewClient 创建新的WebSocket客户端
func NewClient(serverURL string) *Client {
	ctx, cancel := context.WithCancel(context.Background())
	return &Client{
		url:      serverURL,
		send:     make(chan []byte, 256),
		handlers: make(map[string]MessageHandler),
		ctx:      ctx,
		cancel:   cancel,
	}
}

// Connect 连接到WebSocket服务器
func (c *Client) Connect() error {
	u, err := url.Parse(c.url)
	if err != nil {
		return fmt.Errorf("解析URL失败: %v", err)
	}

	dialer := websocket.Dialer{
		HandshakeTimeout: 45 * time.Second,
	}

	conn, _, err := dialer.Dial(u.String(), nil)
	if err != nil {
		return fmt.Errorf("连接失败: %v", err)
	}

	c.mutex.Lock()
	c.conn = conn
	c.connected = true
	c.mutex.Unlock()

	// 启动读写goroutine
	go c.readPump()
	go c.writePump()

	return nil
}

// readPump 处理从WebSocket服务器读取消息
func (c *Client) readPump() {
	defer func() {
		c.mutex.Lock()
		if c.conn != nil {
			c.conn.Close()
		}
		c.connected = false
		c.mutex.Unlock()
	}()

	for {
		select {
		case <-c.ctx.Done():
			return
		default:
			c.mutex.RLock()
			if !c.connected {
				c.mutex.RUnlock()
				return
			}
			c.mutex.RUnlock()

			_, message, err := c.conn.ReadMessage()
			if err != nil {
				log.ErrorLogger.Printf("读取消息失败: %v", err)
				return
			}

			// 解析消息类型
			var msg struct {
				Type    string          `json:"type"`
				Payload json.RawMessage `json:"payload"`
			}
			if err := json.Unmarshal(message, &msg); err != nil {
				log.ErrorLogger.Printf("解析消息失败: %v", err)
				continue
			}

			// 调用对应的处理器
			c.mutex.RLock()
			handler, exists := c.handlers[msg.Type]
			c.mutex.RUnlock()

			if exists {
				if err := handler(msg.Payload); err != nil {
					log.ErrorLogger.Printf("处理消息失败: %v", err)
				}
			}
		}
	}
}

// writePump 处理向WebSocket服务器发送消息
func (c *Client) writePump() {
	defer func() {
		c.mutex.Lock()
		if c.conn != nil {
			c.conn.Close()
		}
		c.connected = false
		c.mutex.Unlock()
	}()

	for {
		select {
		case <-c.ctx.Done():
			return
		case message, ok := <-c.send:
			c.mutex.RLock()
			if !c.connected {
				c.mutex.RUnlock()
				return
			}
			c.mutex.RUnlock()

			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := c.conn.WriteMessage(websocket.TextMessage, message); err != nil {
				log.ErrorLogger.Printf("发送消息失败: %v", err)
				return
			}
		}
	}
}

// Send 发送消息
func (c *Client) Send(msgType string, payload interface{}) error {
	message := struct {
		Type    string      `json:"type"`
		Payload interface{} `json:"payload"`
	}{
		Type:    msgType,
		Payload: payload,
	}

	data, err := json.Marshal(message)
	if err != nil {
		return fmt.Errorf("序列化消息失败: %v", err)
	}

	select {
	case c.send <- data:
		return nil
	default:
		return fmt.Errorf("发送队列已满")
	}
}

// RegisterHandler 注册消息处理器
func (c *Client) RegisterHandler(msgType string, handler MessageHandler) {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	c.handlers[msgType] = handler
}

// Close 关闭连接
func (c *Client) Close() {
	c.cancel()
	c.mutex.Lock()
	defer c.mutex.Unlock()
	if c.conn != nil {
		c.conn.Close()
	}
	c.connected = false
}

// IsConnected 检查是否已连接
func (c *Client) IsConnected() bool {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	return c.connected
}
