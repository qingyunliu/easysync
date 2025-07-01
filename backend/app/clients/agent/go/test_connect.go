package main

import (
	"flag"
	"fmt"
	"log"
	"net/url"
	"os"
	"os/signal"
	"time"

	"github.com/gorilla/websocket"
)

var (
	clientID = flag.Int("client_id", 0, "Client ID")
	server   = flag.String("server", "localhost:5001", "Server address")
)

func main() {
	flag.Parse()

	if *clientID == 0 {
		log.Fatal("client_id is required")
	}

	// 构建 WebSocket URL
	u := url.URL{
		Scheme:   "ws",
		Host:     *server,
		Path:     "/ws/socket.io",
		RawQuery: fmt.Sprintf("client_id=%d", *clientID),
	}

	log.Printf("Connecting to %s", u.String())

	// 创建 WebSocket 连接
	c, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatal("dial:", err)
	}
	defer c.Close()

	// 处理中断信号
	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	// 心跳消息
	heartbeat := time.NewTicker(30 * time.Second)
	defer heartbeat.Stop()

	// 读取消息的 goroutine
	done := make(chan struct{})
	go func() {
		defer close(done)
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				log.Println("read:", err)
				return
			}
			log.Printf("recv: %s", message)
		}
	}()

	// 主循环
	for {
		select {
		case <-done:
			return
		case <-heartbeat.C:
			err := c.WriteMessage(websocket.TextMessage, []byte("heartbeat"))
			if err != nil {
				log.Println("write:", err)
				return
			}
		case <-interrupt:
			log.Println("interrupt")
			err := c.WriteMessage(websocket.CloseMessage, websocket.FormatCloseMessage(websocket.CloseNormalClosure, ""))
			if err != nil {
				log.Println("write close:", err)
				return
			}
			select {
			case <-done:
			case <-time.After(time.Second):
			}
			return
		}
	}
} 
