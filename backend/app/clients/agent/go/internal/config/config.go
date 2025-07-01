package config

import (
	"fmt"
	"os"
	"path/filepath"
	"time"
	"gopkg.in/yaml.v2"
)

// Config 代表Agent配置
type Config struct {
	ServerURL       string        `yaml:"server_url"`
	MonitorInterval time.Duration `yaml:"monitor_interval"`
	SyncConfig      SyncConfig    `yaml:"sync"`
	LogConfig       LogConfig     `yaml:"log"`
}

// SyncConfig 代表同步配置
type SyncConfig struct {
	MaxRetries     int           `yaml:"max_retries"`
	RetryInterval  time.Duration `yaml:"retry_interval"`
	DefaultTimeout time.Duration `yaml:"default_timeout"`
}

// LogConfig 代表日志配置
type LogConfig struct {
	Level      string `yaml:"level"`
	MaxSize    int    `yaml:"max_size"`
	MaxBackups int    `yaml:"max_backups"`
	MaxAge     int    `yaml:"max_age"`
}

// LoadConfig 从文件加载配置
func LoadConfig(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %v", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("解析配置文件失败: %v", err)
	}

	return &cfg, nil
}

// Validate 验证配置
func (c *Config) Validate() error {
	if c.ServerURL == "" {
		return fmt.Errorf("server_url不能为空")
	}
	if c.MonitorInterval <= 0 {
		return fmt.Errorf("monitor_interval必须大于0")
	}
	if c.SyncConfig.MaxRetries < 0 {
		return fmt.Errorf("max_retries不能为负数")
	}
	if c.SyncConfig.RetryInterval <= 0 {
		return fmt.Errorf("retry_interval必须大于0")
	}
	return nil
}

// Reload 重新加载配置
func (c *Config) Reload() error {
	// 重新加载配置
	newCfg, err := LoadConfig(filepath.Join(filepath.Dir(os.Args[0]), "config.yaml"))
	if err != nil {
		return err
	}

	// 验证新配置
	if err := newCfg.Validate(); err != nil {
		return err
	}

	// 更新配置
	*c = *newCfg
	return nil
}
