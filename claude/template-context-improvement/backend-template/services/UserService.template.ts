// UserService.ts - Service template (Keep under 300 lines)

/**
 * AI NOTE: This is a template for a service class.
 * Services contain business logic and coordinate between repositories.
 * Keep methods focused and under 50 lines each.
 * Use dependency injection for testability.
 */

import { User, CreateUserDTO, UpdateUserDTO } from '@/types/user';
import { UserRepository } from '@/repositories/UserRepository';
import { CacheService } from '@/services/CacheService';
import { EmailService } from '@/services/EmailService';
import { AppError, NotFoundError, ValidationError } from '@/utils/errors';
import { logger } from '@/utils/logger';

export class UserService {
  private readonly CACHE_TTL = 300; // 5 minutes
  private readonly CACHE_PREFIX = 'user:';

  constructor(
    private userRepository: UserRepository,
    private cacheService: CacheService,
    private emailService: EmailService
  ) {
    // AI: Dependencies injected for easy testing
  }

  /**
   * Get all users with optional filtering
   * Keep under 30 lines
   */
  async findAll(filters?: { role?: string; active?: boolean }): Promise<User[]> {
    const cacheKey = `${this.CACHE_PREFIX}list:${JSON.stringify(filters || {})}`;
    
    // Check cache first
    const cached = await this.cacheService.get<User[]>(cacheKey);
    if (cached) {
      logger.debug('Cache hit for user list');
      return cached;
    }

    // Fetch from database
    const users = await this.userRepository.findAll(filters);
    
    // Cache the result
    await this.cacheService.set(cacheKey, users, this.CACHE_TTL);
    
    logger.info(`Found ${users.length} users`);
    return users;
  }

  /**
   * Get single user by ID
   * Keep under 25 lines
   */
  async findById(id: string): Promise<User> {
    const cacheKey = `${this.CACHE_PREFIX}${id}`;
    
    // Check cache
    const cached = await this.cacheService.get<User>(cacheKey);
    if (cached) {
      return cached;
    }

    // Fetch from database
    const user = await this.userRepository.findById(id);
    
    if (!user) {
      throw new NotFoundError(`User with ID ${id} not found`);
    }

    // Cache the user
    await this.cacheService.set(cacheKey, user, this.CACHE_TTL);
    
    return user;
  }

  /**
   * Create new user
   * Keep under 50 lines
   */
  async create(data: CreateUserDTO): Promise<User> {
    // Validate input
    await this.validateUserData(data);
    
    // Check if email already exists
    const existing = await this.userRepository.findByEmail(data.email);
    if (existing) {
      throw new ValidationError('Email already registered');
    }

    // Hash password (if applicable)
    const hashedPassword = await this.hashPassword(data.password);
    
    // Create user
    const user = await this.userRepository.create({
      ...data,
      password: hashedPassword
    });
    
    // Send welcome email (async, don't wait)
    this.emailService.sendWelcomeEmail(user.email, user.name)
      .catch(err => logger.error('Failed to send welcome email:', err));
    
    // Invalidate user list cache
    await this.cacheService.deletePattern(`${this.CACHE_PREFIX}list:*`);
    
    logger.info(`Created new user: ${user.id}`);
    return user;
  }

  /**
   * Update existing user
   * Keep under 40 lines
   */
  async update(id: string, data: UpdateUserDTO): Promise<User> {
    // Check user exists
    const existing = await this.findById(id);
    
    // Validate update data
    if (data.email && data.email !== existing.email) {
      const emailTaken = await this.userRepository.findByEmail(data.email);
      if (emailTaken) {
        throw new ValidationError('Email already in use');
      }
    }

    // Update user
    const updated = await this.userRepository.update(id, data);
    
    if (!updated) {
      throw new AppError('Failed to update user');
    }

    // Invalidate caches
    await this.cacheService.delete(`${this.CACHE_PREFIX}${id}`);
    await this.cacheService.deletePattern(`${this.CACHE_PREFIX}list:*`);
    
    logger.info(`Updated user: ${id}`);
    return updated;
  }

  /**
   * Delete user (soft delete)
   * Keep under 30 lines
   */
  async delete(id: string): Promise<void> {
    // Check user exists
    await this.findById(id);
    
    // Perform soft delete
    const deleted = await this.userRepository.softDelete(id);
    
    if (!deleted) {
      throw new AppError('Failed to delete user');
    }

    // Clear all related caches
    await this.cacheService.delete(`${this.CACHE_PREFIX}${id}`);
    await this.cacheService.deletePattern(`${this.CACHE_PREFIX}list:*`);
    
    logger.info(`Deleted user: ${id}`);
  }

  /**
   * Private helper methods
   * Keep each under 20 lines
   */
  private async validateUserData(data: CreateUserDTO): Promise<void> {
    const errors: string[] = [];
    
    if (!data.email || !this.isValidEmail(data.email)) {
      errors.push('Invalid email address');
    }
    
    if (!data.password || data.password.length < 8) {
      errors.push('Password must be at least 8 characters');
    }
    
    if (errors.length > 0) {
      throw new ValidationError('Validation failed', errors);
    }
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  private async hashPassword(password: string): Promise<string> {
    // AI: Implement actual hashing here
    return `hashed_${password}`;
  }
}

// Export singleton instance if needed
export const userService = new UserService(
  new UserRepository(),
  new CacheService(),
  new EmailService()
);